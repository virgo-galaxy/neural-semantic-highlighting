import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

import { type BrowserModel, BrowserRuntime } from "@nsh/browser";
import { createHighlighter } from "@nsh/highlighter/core";
import { afterEach, describe, expect, it, vi } from "vitest";

import { characterMap, SpanDecoder } from "../packages/runtimes/browser/src/decode.js";

const model: BrowserModel = {
  id: "test",
  manifest: { id: "test", documentKinds: [{ id: "javascript", extensions: [".js"] }] },
  modelUrl: () => "https://example.test/model.onnx",
  sha256: "test",
  contextBytes: 512,
  schema: { tokenTypes: ["tag", "string"], modifiers: ["declaration"] },
  modifierThreshold: 0.6,
};
const empty = { offsetEncoding: "utf-16" as const, spans: [] };
class FakeWorker extends EventTarget {
  static instances: FakeWorker[] = [];
  messages: { id: number; source: string; model: unknown }[] = [];
  terminated = false;
  constructor() {
    super();
    FakeWorker.instances.push(this);
  }
  postMessage(value: (typeof this.messages)[number]) {
    this.messages.push(structuredClone(value));
  }
  terminate() {
    this.terminated = true;
  }
  reply(id: number, result = empty) {
    this.dispatchEvent(new MessageEvent("message", { data: { id, result } }));
  }
}
afterEach(() => {
  vi.unstubAllGlobals();
  FakeWorker.instances = [];
});

describe("browser decoder", () => {
  it("maps original UTF-8 characters to UTF-16, preserving CRLF", () => {
    expect(characterMap("A星🌌\r\n")).toEqual({
      bytes: [0, 1, 4, 8, 9, 10],
      units: [0, 1, 2, 4, 5, 6],
    });
    expect(() => characterMap("\ud800")).toThrow("unpaired surrogate");
  });
  it("carries a span across windows, votes over its characters and takes flags at its start", () => {
    const decoder = new SpanDecoder(model);
    decoder.append(0, 1, 1, [4, 0], 0, [2], 0);
    decoder.append(1, 3, 2, [0, 6], 0, [-2], 0);
    decoder.append(3, 4, 0, [0, 0], 0, [0], 0);
    expect(decoder.finish()).toEqual({
      offsetEncoding: "utf-16",
      spans: [{ start: 0, end: 3, tokenType: "string", modifiers: ["declaration"] }],
    });
  });
  it("recovers orphan I labels and applies only the model's declared coalescing and modifier policy", () => {
    const decoder = new SpanDecoder({
      ...model,
      decoder: {
        coalesceAdjacentTokenTypes: ["string"],
        modifierRoles: { declaration: ["tag"] },
      },
    });
    decoder.append(0, 1, 2, [0, 4], 0, [4], 0);
    decoder.append(1, 2, 1, [0, 4], 0, [4], 0);
    decoder.append(2, 3, 1, [4, 0], 0, [4], 0);
    expect(decoder.finish().spans).toEqual([
      { start: 0, end: 2, tokenType: "string" },
      { start: 2, end: 3, tokenType: "tag", modifiers: ["declaration"] },
    ]);
  });
});

describe("browser runtime lifecycle", () => {
  it("handles empty input and validation without creating a worker", async () => {
    const runtime = new BrowserRuntime();
    const pack = runtime.createPack(model);
    expect(await pack.highlight({ source: "", documentKind: "javascript" })).toEqual(empty);
    await expect(pack.highlight({ source: "x", documentKind: "other" })).rejects.toThrow(
      "Unsupported",
    );
    runtime.close();
    await expect(pack.highlight({ source: "", documentKind: "javascript" })).rejects.toThrow(
      "closed",
    );
  });
  it("correlates concurrent responses, strips model functions and rejects pending work on close", async () => {
    vi.stubGlobal("Worker", FakeWorker);
    const runtime = new BrowserRuntime();
    const pack = runtime.createPack({ ...model, dependencies: [model] });
    const first = pack.highlight({ source: "first", documentKind: "javascript" });
    const second = pack.highlight({ source: "second", documentKind: "javascript" });
    const worker = FakeWorker.instances[0];
    expect(worker.messages).toHaveLength(2);
    expect(worker.messages[0].model).not.toHaveProperty("dependencies");
    worker.reply(worker.messages[1].id);
    expect(await second).toEqual(empty);
    const rejected = expect(first).rejects.toThrow("closed");
    runtime.close();
    await rejected;
    expect(worker.terminated).toBe(true);
  });
  it("propagates load/inference errors and can recover from a crashed worker", async () => {
    vi.stubGlobal("Worker", FakeWorker);
    const runtime = new BrowserRuntime();
    const pack = runtime.createPack(model);
    const first = pack.highlight({ source: "x", documentKind: "javascript" });
    const worker = FakeWorker.instances[0];
    worker.dispatchEvent(
      new MessageEvent("message", {
        data: { id: worker.messages[0].id, error: "Model integrity mismatch" },
      }),
    );
    await expect(first).rejects.toThrow("integrity mismatch");
    const second = pack.highlight({ source: "y", documentKind: "javascript" });
    const rejected = expect(second).rejects.toThrow("worker failed");
    worker.dispatchEvent(new Event("error"));
    await rejected;
    const third = pack.highlight({ source: "z", documentKind: "javascript" });
    expect(FakeWorker.instances).toHaveLength(2);
    FakeWorker.instances[1].reply(FakeWorker.instances[1].messages[0].id);
    expect(await third).toEqual(empty);
    runtime.close();
  });
});

describe("consumer API", () => {
  it("resolves aliases and escapes rendered source", async () => {
    vi.stubGlobal("Worker", FakeWorker);
    const highlighter = createHighlighter({ languages: [model] });
    expect(highlighter.supports("JS")).toBe(true);
    const pending = highlighter.highlight("<script>&", { language: "js" });
    const worker = FakeWorker.instances[0];
    worker.reply(worker.messages[0].id);
    const result = await pending;
    expect(result.value).toBe("&lt;script&gt;&amp;");
    expect(result.html).toBe(
      '<pre class="nsh" data-language="javascript"><code>&lt;script&gt;&amp;</code></pre>',
    );
    await expect(highlighter.highlight("x", { language: "unknown" })).rejects.toThrow();
    highlighter.close();
  });
});

describe("shipped browser artifacts", () => {
  it("matches reviewed export hashes, descriptors and the preserved native weights", async () => {
    for (const id of [
      "typescript",
      "go",
      "css",
      "html",
      "vue",
      "python",
      "bash",
      "perl",
      "awk",
      "sql",
      "powershell",
      "bat",
      "assembly",
      "java",
      "csharp",
      "c",
      "cpp",
      "php",
    ]) {
      const metadata = JSON.parse(readFileSync(`packs/${id}/browser/model.json`, "utf8"));
      const verification = JSON.parse(
        readFileSync(`packs/${id}/browser/verification.json`, "utf8"),
      );
      const { default: descriptor } = (await import(
        `../packages/highlighter/src/languages/${id}.ts`
      )) as { default: BrowserModel };
      const hash = (path: string) => createHash("sha256").update(readFileSync(path)).digest("hex");
      expect(hash(metadata.source.file)).toBe(metadata.source.sha256);
      expect(hash(`packs/${id}/browser/model.onnx`)).toBe(metadata.model.sha256);
      expect(hash(`packages/highlighter/dist/models/${id}.onnx`)).toBe(metadata.model.sha256);
      expect(descriptor.sha256).toBe(metadata.model.sha256);
      expect(descriptor.schema).toEqual(metadata.schema);
      expect(descriptor.decoder).toEqual(metadata.decoder);
      expect(descriptor.manifest).toEqual(metadata.manifest);
      expect(descriptor.modifierThreshold).toBe(metadata.modifierThreshold);
      expect(verification.sourceSha256).toBe(metadata.source.sha256);
      expect(verification.modelSha256).toBe(metadata.model.sha256);
      for (const comparison of verification.comparisons)
        expect(Math.max(...comparison.maxAbsoluteErrors)).toBeLessThan(1e-4);
    }
  });
});
