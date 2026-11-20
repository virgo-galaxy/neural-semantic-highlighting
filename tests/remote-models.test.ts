import { readFileSync } from "node:fs";

import type { HighlightResult } from "@nsh/core";
import { createHighlighter, type ModelAssetRequest } from "@nsh/highlighter";
import typescript from "@nsh/models/languages/typescript";
import { afterEach, describe, expect, it, vi } from "vitest";

import { modelAssets } from "../packages/highlighter/src/model-assets.js";

class RemoteWorker extends EventTarget {
  static instances: RemoteWorker[] = [];
  messages: { id: number; source: string; model: { id: string; modelUrl: string } }[] = [];
  terminated = false;
  constructor() {
    super();
    RemoteWorker.instances.push(this);
  }
  postMessage(message: RemoteWorker["messages"][number]) {
    this.messages.push(structuredClone(message));
  }
  terminate() {
    this.terminated = true;
  }
  reply(result: HighlightResult = { offsetEncoding: "utf-16", spans: [] }, error?: string) {
    this.dispatchEvent(
      new MessageEvent("message", { data: { id: this.messages.at(-1)!.id, result, error } }),
    );
  }
}

function metadataResponse(id: string) {
  return new Response(Uint8Array.from(readFileSync(`packs/${id}/browser/model.json`)).buffer);
}
function setupFetch() {
  const fetcher = vi.fn(async (value: string | URL) => {
    const asset = modelAssets.find((asset) =>
      new URL(value).pathname.endsWith(asset.metadata.path),
    );
    if (!asset) throw new Error(`Unexpected metadata request: ${value}`);
    return metadataResponse(asset.id);
  });
  vi.stubGlobal("fetch", fetcher);
  vi.stubGlobal("Worker", RemoteWorker);
  return fetcher;
}
async function messageCount(count: number) {
  await vi.waitFor(() => expect(RemoteWorker.instances[0]?.messages.length).toBe(count));
  return RemoteWorker.instances[0]!;
}
afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  RemoteWorker.instances = [];
});

describe("remote model delivery", () => {
  it("resolves an application-relative resource directory against the document URL", async () => {
    const fetcher = setupFetch();
    vi.stubGlobal("document", { baseURI: "https://app.test/docs/page/" });
    const highlighter = createHighlighter({ modelBaseUrl: "/resources", languages: ["ts"] });
    const result = highlighter.highlight("const x = 1", { language: "ts" });
    (await messageCount(1)).reply();
    await result;
    expect(String(fetcher.mock.calls[0][0])).toMatch(/^https:\/\/app\.test\/resources\/v1\//);
    highlighter.close();
  });
  it("registers aliases and dependencies without fetching on creation or empty input", async () => {
    const fetcher = setupFetch();
    const highlighter = createHighlighter({
      modelBaseUrl: "https://models.test/bucket/prefix",
      languages: ["Vue", "SVG"],
    });
    for (const name of ["vue", "tsx", "scss", "less", "xml", "svg"])
      expect(highlighter.supports(name)).toBe(true);
    expect(highlighter.supports("python")).toBe(false);
    expect(highlighter.supports("react")).toBe(false);
    await expect(highlighter.highlightTokens({ source: "", documentKind: "vue" })).resolves.toEqual(
      { offsetEncoding: "utf-16", spans: [] },
    );
    expect(fetcher).not.toHaveBeenCalled();
    expect(RemoteWorker.instances).toHaveLength(0);
    highlighter.close();
  });

  it("retains every selected decoder, schema, window policy and metadata hash remotely", async () => {
    const fetcher = setupFetch();
    const highlighter = createHighlighter({ modelBaseUrl: "https://models.test/bucket/prefix" });
    for (const [index, asset] of modelAssets.entries()) {
      const documentKind = asset.manifest.documentKinds[0].id;
      const result = highlighter.highlightTokens({ source: "x", documentKind });
      const worker = await messageCount(index + 1);
      const metadata = JSON.parse(readFileSync(`packs/${asset.id}/browser/model.json`, "utf8"));
      expect(worker.messages.at(-1)?.model).toMatchObject({
        id: asset.id,
        sha256: asset.sha256,
        modelUrl: `https://models.test/bucket/prefix/${asset.path}`,
        schema: metadata.schema,
        contextBytes: metadata.contextBytes,
        modifierThreshold: metadata.modifierThreshold,
        decoder: metadata.decoder,
      });
      const actual = worker.messages.at(-1)!.model as unknown as Record<string, unknown>;
      expect(actual.structuredDecoder).toEqual(metadata.structuredDecoder);
      expect(actual.inferenceWindowing).toEqual(metadata.inferenceWindowing);
      worker.reply();
      await result;
    }
    expect(fetcher).toHaveBeenCalledTimes(40);
    highlighter.close();
  });

  it("deduplicates metadata and signed URL resolution and refreshes a failed model URL", async () => {
    const fetcher = setupFetch();
    const resolver = vi.fn(
      async (asset: ModelAssetRequest) =>
        `https://private.test/${asset.path}?signature=${resolver.mock.calls.length}`,
    );
    const highlighter = createHighlighter({ resolveAssetUrl: resolver, languages: ["TSX"] });
    const first = highlighter.highlight("const a = 1", { language: "ts" });
    const second = highlighter.highlight("const b = 2", { language: "js" });
    const worker = await messageCount(2);
    const [a, b] = worker.messages;
    expect(a.model.modelUrl).toBe(b.model.modelUrl);
    for (const item of [a, b])
      worker.dispatchEvent(
        new MessageEvent("message", {
          data: { id: item.id, result: { offsetEncoding: "utf-16", spans: [] } },
        }),
      );
    await Promise.all([first, second]);
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(resolver).toHaveBeenCalledTimes(2);
    const failed = highlighter.highlight("const c = 3", { language: "tsx" });
    const rejected = expect(failed).rejects.toThrow("expired");
    await messageCount(3);
    worker.reply(undefined, "expired");
    await rejected;
    const retry = highlighter.highlight("const c = 3", { language: "tsx" });
    await messageCount(4);
    worker.reply();
    await retry;
    expect(resolver.mock.calls.map(([request]) => request.kind)).toEqual([
      "metadata",
      "model",
      "model",
    ]);
    expect(fetcher).toHaveBeenCalledTimes(1);
    highlighter.close();
  });

  it("rejects altered metadata before inference and allows a later retry", async () => {
    const fetcher = setupFetch();
    fetcher.mockResolvedValueOnce(new Response("{}"));
    const highlighter = createHighlighter({
      modelBaseUrl: "https://models.test/",
      languages: ["ts"],
    });
    await expect(highlighter.highlight("const x = 1", { language: "ts" })).rejects.toThrow(
      "metadata integrity mismatch",
    );
    expect(RemoteWorker.instances).toHaveLength(0);
    const result = highlighter.highlight("const x = 1", { language: "ts" });
    (await messageCount(1)).reply();
    await result;
    expect(fetcher).toHaveBeenCalledTimes(2);
    highlighter.close();
  });

  it("surfaces HTTP metadata errors without creating a worker", async () => {
    const fetcher = setupFetch();
    fetcher.mockResolvedValueOnce(new Response("", { status: 404 }));
    const highlighter = createHighlighter({
      modelBaseUrl: "https://models.test/",
      languages: ["ts"],
    });
    await expect(highlighter.highlight("x", { language: "ts" })).rejects.toThrow("metadata (404)");
    expect(RemoteWorker.instances).toHaveLength(0);
    highlighter.close();
  });

  it("rejects pending metadata work immediately on close and never starts a late worker", async () => {
    const hashing = vi.spyOn(crypto.subtle, "digest");
    let complete!: (response: Response) => void;
    vi.stubGlobal(
      "fetch",
      vi.fn(
        () =>
          new Promise<Response>((resolve) => {
            complete = resolve;
          }),
      ),
    );
    vi.stubGlobal("Worker", RemoteWorker);
    const highlighter = createHighlighter({
      modelBaseUrl: "https://models.test/",
      languages: ["ts"],
    });
    const result = highlighter.highlight("x", { language: "ts" });
    const rejected = expect(result).rejects.toThrow("closed");
    await vi.waitFor(() => expect(complete).toBeTypeOf("function"));
    highlighter.close();
    await rejected;
    complete(metadataResponse("typescript"));
    await vi.waitFor(() => expect(hashing).toHaveBeenCalledOnce());
    await hashing.mock.results[0].value;
    await expect(highlighter.highlight("", { language: "ts" })).rejects.toThrow("closed");
    expect(RemoteWorker.instances).toHaveLength(0);
  });

  it("rejects pending signatures on close and does not post after the signature arrives", async () => {
    setupFetch();
    let finish!: (url: string) => void;
    const highlighter = createHighlighter({
      languages: ["ts"],
      resolveAssetUrl: (asset) =>
        asset.kind === "metadata"
          ? `https://models.test/${asset.path}`
          : new Promise<string>((resolve) => {
              finish = resolve;
            }),
    });
    const result = highlighter.highlight("x", { language: "ts" });
    const rejected = expect(result).rejects.toThrow("closed");
    await vi.waitFor(() => expect(finish).toBeTypeOf("function"));
    highlighter.close();
    await rejected;
    finish("https://models.test/late.onnx");
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(RemoteWorker.instances).toHaveLength(0);
  });

  it("rejects ambiguous configuration, unknown names and non-HTTP URLs", async () => {
    setupFetch();
    expect(() => createHighlighter({ languages: ["ts"] })).toThrow("modelBaseUrl");
    expect(() =>
      createHighlighter({ modelBaseUrl: "https://models.test", languages: [typescript] }),
    ).toThrow("content IDs");
    expect(() =>
      createHighlighter({ modelBaseUrl: "https://models.test", languages: ["__proto__"] }),
    ).toThrow("Unsupported");
    const highlighter = createHighlighter({
      languages: ["ts"],
      resolveAssetUrl: () => "file:///model.onnx",
    });
    await expect(highlighter.highlight("x", { language: "ts" })).rejects.toThrow("HTTP or HTTPS");
    highlighter.close();
  });
});
