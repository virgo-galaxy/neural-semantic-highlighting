import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

import { type BrowserModel, BrowserRuntime } from "@nsh/browser";
import type { HighlightResult } from "@nsh/core";
import { createHighlighter } from "@nsh/highlighter/core";
import dart from "@nsh/highlighter/languages/dart";
import dockerfile from "@nsh/highlighter/languages/dockerfile";
import dotenv from "@nsh/highlighter/languages/dotenv";
import flutter from "@nsh/highlighter/languages/flutter";
import ini from "@nsh/highlighter/languages/ini";
import json from "@nsh/highlighter/languages/json";
import jsonc from "@nsh/highlighter/languages/jsonc";
import kotlin from "@nsh/highlighter/languages/kotlin";
import makefile from "@nsh/highlighter/languages/makefile";
import markdown from "@nsh/highlighter/languages/markdown";
import ruby from "@nsh/highlighter/languages/ruby";
import svg from "@nsh/highlighter/languages/svg";
import toml from "@nsh/highlighter/languages/toml";
import typescript from "@nsh/highlighter/languages/typescript";
import xml from "@nsh/highlighter/languages/xml";
import yaml from "@nsh/highlighter/languages/yaml";
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
  reply(id: number, result: HighlightResult = empty) {
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
  it("routes Makefile filenames and aliases to one standalone model", async () => {
    vi.stubGlobal("Worker", FakeWorker);
    const highlighter = createHighlighter({ languages: [makefile] });
    expect(highlighter.languages()).toEqual(["makefile"]);
    for (const name of ["makefile", "Makefile", "make", "mk", "mak", "gnumake", "GNUmakefile"]) {
      expect(highlighter.supports(name)).toBe(true);
      const pending = highlighter.highlight("all:\n\t@echo ready\n", { language: name });
      const worker = FakeWorker.instances[0]!;
      const request = worker.messages.at(-1)!;
      expect(request.model).toMatchObject({ id: "makefile" });
      worker.reply(request.id);
      expect((await pending).language).toBe("makefile");
    }
    expect(highlighter.supports("cmake")).toBe(false);
    highlighter.close();
  });
  it("routes Dockerfile and Containerfile aliases to one standalone model", async () => {
    vi.stubGlobal("Worker", FakeWorker);
    const highlighter = createHighlighter({ languages: [dockerfile] });
    expect(highlighter.languages()).toEqual(["dockerfile"]);
    for (const name of [
      "dockerfile",
      "Dockerfile",
      "docker",
      "Docker",
      "containerfile",
      "Containerfile",
    ]) {
      expect(highlighter.supports(name)).toBe(true);
      const pending = highlighter.highlight("FROM scratch\n", { language: name });
      const worker = FakeWorker.instances[0]!;
      const request = worker.messages.at(-1)!;
      expect(request.model).toMatchObject({ id: "dockerfile" });
      worker.reply(request.id);
      expect((await pending).language).toBe("dockerfile");
    }
    expect(highlighter.supports("compose")).toBe(false);
    highlighter.close();
  });
  it("routes Markdown aliases and reuses only a registered predicted fence language", async () => {
    vi.stubGlobal("Worker", FakeWorker);
    const highlighter = createHighlighter({ languages: [markdown, typescript] });
    for (const name of ["markdown", "Markdown", "md", "MD", "mdown", "mkd"])
      expect(highlighter.supports(name)).toBe(true);
    const source = "```JS\nconst x = 1;\n```";
    const pending = highlighter.highlight(source, { language: "MD" });
    const worker = FakeWorker.instances[0]!;
    expect(worker.messages[0].model).toMatchObject({ id: "markdown" });
    worker.reply(worker.messages[0].id, {
      offsetEncoding: "utf-16",
      spans: [
        { start: 0, end: 3, tokenType: "code-fence" },
        { start: 3, end: 5, tokenType: "code-language" },
        { start: 6, end: 19, tokenType: "embedded-code" },
        { start: 19, end: 22, tokenType: "code-fence" },
      ],
    });
    await vi.waitFor(() => expect(worker.messages).toHaveLength(2));
    expect(worker.messages[1].model).toMatchObject({ id: "typescript" });
    expect(worker.messages[1].source).toBe("const x = 1;\n");
    worker.reply(worker.messages[1].id, {
      offsetEncoding: "utf-16",
      spans: [{ start: 0, end: 5, tokenType: "keyword" }],
    });
    const output = await pending;
    expect(output.language).toBe("markdown");
    expect(output.result.spans).toContainEqual({
      start: 6,
      end: 11,
      tokenType: "keyword",
      documentKind: "javascript",
    });
    expect(output.html).toContain('data-nsh-language="javascript"');
    highlighter.close();
  });
  it("preserves XML and SVG kinds through one shared model and escapes graphic source", async () => {
    vi.stubGlobal("Worker", FakeWorker);
    const highlighter = createHighlighter({ languages: [xml, svg] });
    expect(svg).toBe(xml);
    expect(highlighter.languages()).toEqual(["xml", "svg"]);
    const source = '<svg><script>alert("source")</script></svg>';
    for (const language of ["xml", "XML", "svg", "SVG"]) {
      expect(highlighter.supports(language)).toBe(true);
      const pending = highlighter.highlight(source, { language });
      const worker = FakeWorker.instances[0]!;
      const message = worker.messages.at(-1)!;
      expect(message.model).toMatchObject({ id: "xml", sha256: xml.sha256 });
      worker.reply(message.id);
      const rendered = await pending;
      expect(rendered.language).toBe(language.toLowerCase());
      expect(rendered.html).toContain("&lt;svg&gt;");
      expect(rendered.html).not.toContain("<script>");
    }
    expect(FakeWorker.instances).toHaveLength(1);
    highlighter.close();
  });
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
  it("routes Flutter and Dart through the same descriptor, model and canonical offsets", async () => {
    vi.stubGlobal("Worker", FakeWorker);
    expect(flutter).toBe(dart);
    const highlighter = createHighlighter({ languages: [flutter, dart] });
    expect(highlighter.languages()).toEqual(["dart"]);
    expect(highlighter.supports("Flutter")).toBe(true);
    const pending = highlighter.highlight("Widget f() => Text('<🌌>');", { language: "flutter" });
    const worker = FakeWorker.instances[0];
    expect(worker.messages[0].model).toMatchObject({ id: "dart", sha256: dart.sha256 });
    worker.reply(worker.messages[0].id);
    const result = await pending;
    expect(result.language).toBe("dart");
    expect(result.html).toContain('data-language="dart"');
    expect(result.value).toContain("&lt;🌌&gt;");
    const tokens = highlighter.highlightTokens({ source: "const x = 1;", documentKind: "flutter" });
    expect(FakeWorker.instances).toHaveLength(1);
    worker.reply(worker.messages[1].id);
    await expect(tokens).resolves.toEqual(empty);
    highlighter.close();
  });
  it("routes Kotlin file and script aliases through one model", async () => {
    vi.stubGlobal("Worker", FakeWorker);
    const highlighter = createHighlighter({ languages: [kotlin] });
    expect(highlighter.languages()).toEqual(["kotlin"]);
    for (const language of ["Kotlin", "kt", "kts", "kotlin-script"]) {
      expect(highlighter.supports(language)).toBe(true);
      const pending = highlighter.highlight('val title = "<星🌌>"', { language });
      const worker = FakeWorker.instances[0];
      const message = worker.messages.at(-1)!;
      expect(message.model).toMatchObject({ id: "kotlin", sha256: kotlin.sha256 });
      worker.reply(message.id);
      const rendered = await pending;
      expect(rendered.language).toBe("kotlin");
      expect(rendered.value).toContain("&lt;星🌌&gt;");
    }
    expect(FakeWorker.instances).toHaveLength(1);
    highlighter.close();
  });
  it("preserves explicit JSON and JSONC kinds while sharing one model", async () => {
    vi.stubGlobal("Worker", FakeWorker);
    const highlighter = createHighlighter({ languages: [json, jsonc] });
    expect(jsonc).toBe(json);
    expect(highlighter.languages()).toEqual(["json", "jsonc"]);
    for (const language of ["json", "JSON", "jsonc", "JSONC"]) {
      expect(highlighter.supports(language)).toBe(true);
      const pending = highlighter.highlight('{"title":"<星🌌>"}', { language });
      const worker = FakeWorker.instances[0];
      const message = worker.messages.at(-1)!;
      expect(message.model).toMatchObject({ id: "json", sha256: json.sha256 });
      worker.reply(message.id);
      const rendered = await pending;
      expect(rendered.language).toBe(language.toLowerCase());
      expect(rendered.value).toContain("&lt;星🌌&gt;");
    }
    expect(FakeWorker.instances).toHaveLength(1);
    highlighter.close();
  });
  it("routes YAML and yml aliases through the same model", async () => {
    vi.stubGlobal("Worker", FakeWorker);
    const highlighter = createHighlighter({ languages: [yaml] });
    expect(highlighter.languages()).toEqual(["yaml"]);
    for (const language of ["yaml", "YAML", "yml", "YML"]) {
      expect(highlighter.supports(language)).toBe(true);
      const pending = highlighter.highlight('title: "<星🌌>"', { language });
      const worker = FakeWorker.instances[0];
      const message = worker.messages.at(-1)!;
      expect(message.model).toMatchObject({ id: "yaml", sha256: yaml.sha256 });
      worker.reply(message.id);
      const rendered = await pending;
      expect(rendered.language).toBe("yaml");
      expect(rendered.value).toContain("&lt;星🌌&gt;");
    }
    expect(FakeWorker.instances).toHaveLength(1);
    highlighter.close();
  });
  it("routes TOML names through its selected model", async () => {
    vi.stubGlobal("Worker", FakeWorker);
    const highlighter = createHighlighter({ languages: [toml] });
    expect(highlighter.languages()).toEqual(["toml"]);
    for (const language of ["toml", "TOML"]) {
      expect(highlighter.supports(language)).toBe(true);
      const pending = highlighter.highlight('title = "<星🌌>"', { language });
      const worker = FakeWorker.instances[0];
      const message = worker.messages.at(-1)!;
      expect(message.model).toMatchObject({ id: "toml", sha256: toml.sha256 });
      worker.reply(message.id);
      const rendered = await pending;
      expect(rendered.language).toBe("toml");
      expect(rendered.value).toContain("&lt;星🌌&gt;");
    }
    expect(FakeWorker.instances).toHaveLength(1);
    highlighter.close();
  });
  it("routes Dotenv names through its selected model", async () => {
    vi.stubGlobal("Worker", FakeWorker);
    const highlighter = createHighlighter({ languages: [dotenv] });
    expect(highlighter.languages()).toEqual(["dotenv"]);
    for (const language of ["dotenv", "Dotenv", "env", "ENV", ".env"]) {
      expect(highlighter.supports(language)).toBe(true);
      const pending = highlighter.highlight('title = "<星🌌>"', { language });
      const worker = FakeWorker.instances[0];
      const message = worker.messages.at(-1)!;
      expect(message.model).toMatchObject({ id: "dotenv", sha256: dotenv.sha256 });
      worker.reply(message.id);
      const rendered = await pending;
      expect(rendered.language).toBe("dotenv");
      expect(rendered.value).toContain("&lt;星🌌&gt;");
    }
    expect(FakeWorker.instances).toHaveLength(1);
    highlighter.close();
  });
  it("routes INI names through its selected model", async () => {
    vi.stubGlobal("Worker", FakeWorker);
    const highlighter = createHighlighter({ languages: [ini] });
    expect(highlighter.languages()).toEqual(["ini"]);
    for (const language of ["ini", "INI", "cfg", "CFG", "editorconfig", "EditorConfig"]) {
      expect(highlighter.supports(language)).toBe(true);
      const pending = highlighter.highlight('title = "<星🌌>"', { language });
      const worker = FakeWorker.instances[0];
      const message = worker.messages.at(-1)!;
      expect(message.model).toMatchObject({ id: "ini", sha256: ini.sha256 });
      worker.reply(message.id);
      const rendered = await pending;
      expect(rendered.language).toBe("ini");
      expect(rendered.value).toContain("&lt;星🌌&gt;");
    }
    expect(FakeWorker.instances).toHaveLength(1);
    highlighter.close();
  });
  it("routes Ruby source and build-file aliases through one descriptor", async () => {
    vi.stubGlobal("Worker", FakeWorker);
    const highlighter = createHighlighter({ languages: [ruby] });
    expect(highlighter.languages()).toEqual(["ruby"]);
    for (const language of ["Ruby", "rb", "rake", "gemspec", "Gemfile", "Rakefile"]) {
      expect(highlighter.supports(language)).toBe(true);
      const pending = highlighter.highlight('puts "<星🌌>"', { language });
      const worker = FakeWorker.instances[0];
      const message = worker.messages.at(-1)!;
      expect(message.model).toMatchObject({ id: "ruby", sha256: ruby.sha256 });
      worker.reply(message.id);
      const rendered = await pending;
      expect(rendered.language).toBe("ruby");
      expect(rendered.value).toContain("&lt;星🌌&gt;");
    }
    expect(FakeWorker.instances).toHaveLength(1);
    highlighter.close();
  });
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
      "svelte",
      "rust",
      "zig",
      "dart",
      "swift",
      "kotlin",
      "r",
      "scala",
      "ruby",
      "lua",
      "json",
      "yaml",
      "toml",
      "ini",
      "dotenv",
      "xml",
      "markdown",
      "dockerfile",
      "makefile",
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
      expect(descriptor.structuredDecoder).toEqual(metadata.structuredDecoder);
      expect(descriptor.manifest).toEqual(metadata.manifest);
      expect(descriptor.modifierThreshold).toBe(metadata.modifierThreshold);
      expect(verification.sourceSha256).toBe(metadata.source.sha256);
      expect(verification.modelSha256).toBe(metadata.model.sha256);
      for (const comparison of verification.comparisons)
        expect(Math.max(...comparison.maxAbsoluteErrors)).toBeLessThan(1e-4);
    }
  });
});
