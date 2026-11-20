import { createHash } from "node:crypto";
import { readdirSync, readFileSync } from "node:fs";

import { contentTypes } from "@nsh/core/catalog";
import { createHighlighter } from "@nsh/highlighter";
import compatibility from "@nsh/highlighter/languages/typescript";
import { allModels } from "@nsh/models";
import typescript from "@nsh/models/languages/typescript";
import { describe, expect, it } from "vitest";

import { modelAssets } from "../packages/highlighter/src/model-assets.js";

describe("separate model resources", () => {
  it("keeps the main package free of weights and the resource peer optional", () => {
    expect(compatibility).toBe(typescript);
    const manifest = JSON.parse(readFileSync("packages/highlighter/package.json", "utf8"));
    expect(manifest.dependencies["@nsh/models"]).toBeUndefined();
    expect(manifest.peerDependenciesMeta["@nsh/models"].optional).toBe(true);
    expect(
      readdirSync("packages/highlighter/dist", { recursive: true }).some((name) =>
        String(name).endsWith(".onnx"),
      ),
    ).toBe(false);
    const highlighter = createHighlighter({ languages: [typescript] });
    expect(highlighter.supports("tsx")).toBe(true);
    expect(highlighter.supports("css")).toBe(false);
    highlighter.close();
  });

  it("pins all selected model metadata, content variants and composition dependencies", () => {
    expect(allModels).toHaveLength(40);
    expect(new Set(modelAssets.map((asset) => asset.id))).toEqual(
      new Set(contentTypes.map((entry) => entry.modelId)),
    );
    for (const asset of modelAssets) {
      const model = allModels.find((model) => model.id === asset.id)!;
      const raw = readFileSync(`packs/${asset.id}/browser/model.json`);
      const metadata = JSON.parse(raw.toString());
      expect(createHash("sha256").update(raw).digest("hex")).toBe(asset.metadata.sha256);
      expect(asset.manifest).toEqual(model.manifest);
      expect(model.sha256).toBe(asset.sha256);
      expect(model.contextBytes).toBe(metadata.contextBytes);
      expect(model.inferenceWindowing).toEqual(metadata.inferenceWindowing);
      expect(model.structuredDecoder).toEqual(metadata.structuredDecoder);
      expect(model.dependencies?.map((child) => child.id) ?? []).toEqual(asset.dependencies);
      const catalogDependencies = new Set(
        contentTypes
          .filter((entry) => entry.modelId === asset.id)
          .flatMap((entry) => entry.modelDependencies ?? []),
      );
      expect(new Set(asset.dependencies)).toEqual(catalogDependencies);
    }
  });
});
