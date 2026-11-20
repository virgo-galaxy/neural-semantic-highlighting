import { readdirSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { normalizeLanguageId as normalizeCore } from "@nsh/core";
import {
  contentCategories,
  contentTypes,
  documentKindForFilename,
  getContentType,
  normalizeLanguageId,
} from "@nsh/highlighter/catalog";
import { describe, expect, it } from "vitest";

describe("content catalog", () => {
  it("covers the registered model contracts without exposing file variants as content entries", () => {
    const modelIds = new Set(contentTypes.map((entry) => entry.modelId));
    const packIds = readdirSync("packs", { withFileTypes: true })
      .filter((item) => item.isDirectory())
      .filter((item) => {
        try {
          readFileSync(`packs/${item.name}/manifest.json`);
          return true;
        } catch {
          return false;
        }
      })
      .map((item) => item.name);
    expect([...modelIds].sort()).toEqual(packIds.sort());
    expect(contentCategories.map((category) => category.id)).toEqual(["code", "formats"]);
    for (const entry of contentTypes) {
      const manifest = JSON.parse(readFileSync(`packs/${entry.modelId}/manifest.json`, "utf8"));
      const supported = manifest.documentKinds.map((kind: { id: string }) => kind.id);
      expect(supported).toContain(normalizeLanguageId(entry.id));
      for (const alias of entry.aliases) {
        expect(normalizeCore(alias.toUpperCase())).toBe(normalizeLanguageId(entry.id));
        expect(getContentType(alias)).toBe(entry);
        expect(contentTypes.some((other) => other.id === alias)).toBe(false);
      }
      for (const variant of entry.fileVariants ?? []) {
        expect(supported).toContain(variant.id);
        expect(contentTypes.some((other) => other.id === variant.id)).toBe(false);
      }
    }
    expect(getContentType("tsx")?.modelId).toBe("typescript");
    expect(getContentType("scss")?.modelId).toBe("css");
    expect(getContentType("svg")?.modelId).toBe("xml");
    expect(getContentType("flutter")?.modelId).toBe("dart");
    expect(getContentType("graphql")?.category).toBe("code");
    expect(getContentType("dockerfile")?.category).toBe("formats");
  });

  it("accepts registered shorthand names without guessing unsupported names", () => {
    for (const name of ["js", "JS", "JavaScript"]) expect(normalizeCore(name)).toBe("javascript");
    for (const name of ["ts", "TS", "TypeScript"]) expect(normalizeCore(name)).toBe("typescript");
    expect(normalizeCore("Flutter")).toBe("dart");
    expect(normalizeCore("ZSH")).toBe("bash");
    for (const name of ["__proto__", "constructor", "react", ".tsx", "english"]) {
      expect(getContentType(name)).toBeUndefined();
      expect(normalizeCore(name)).toBe(name);
    }
  });

  it("resolves filename variants while honoring explicit JSONC and source-family choices", () => {
    expect(documentKindForFilename("types.d.ts", "typescript")).toBe("typescript-declaration");
    expect(documentKindForFilename("types.d.mts", "typescript")).toBe("typescript-esm-declaration");
    expect(documentKindForFilename("App.tsx", "typescript")).toBe("tsx");
    expect(documentKindForFilename("app.mjs", "javascript")).toBe("javascript-esm");
    expect(documentKindForFilename("tsconfig.json", "jsonc")).toBe("jsonc");
    expect(documentKindForFilename(".env.local", "dotenv")).toBe("dotenv");
    expect(documentKindForFilename("functions.sh", "shell")).toBe("bash");
    expect(documentKindForFilename("header.h", "cpp")).toBe("cpp");
    expect(documentKindForFilename(".editorconfig", "ini")).toBe("ini");
    expect(documentKindForFilename("hello.dart", "flutter")).toBe("dart");
    expect(documentKindForFilename("unknown.xyz")).toBeUndefined();
    expect(documentKindForFilename("hello.ts", "unknown")).toBeUndefined();
  });

  it("keeps all grouped Playground samples discoverable with valid model routing", () => {
    const folder = resolve("apps/playground/src/views/highlighter/examples");
    let count = 0;
    for (const category of contentCategories) {
      for (const directory of readdirSync(resolve(folder, category.id))) {
        const entry = getContentType(directory);
        expect(entry?.category).toBe(category.id);
        const manifest = JSON.parse(readFileSync(`packs/${entry!.modelId}/manifest.json`, "utf8"));
        for (const filename of readdirSync(resolve(folder, category.id, directory))) {
          expect(manifest.documentKinds.map((kind: { id: string }) => kind.id)).toContain(
            documentKindForFilename(filename, directory),
          );
          count++;
        }
      }
    }
    expect(count).toBeGreaterThan(300);
  });
});
