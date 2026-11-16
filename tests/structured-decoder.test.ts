import { readFileSync } from "node:fs";

import type { BrowserModel } from "@nsh/browser";
import { describe, expect, it } from "vitest";

import { characterMap } from "../packages/runtimes/browser/src/decode.js";
import { StructuredSpanDecoder } from "../packages/runtimes/browser/src/structured.js";

const fixture = JSON.parse(
  readFileSync(new URL("./fixtures/joint-bio.json", import.meta.url), "utf8"),
);
const model: BrowserModel = {
  id: "fixture",
  manifest: { id: "fixture", documentKinds: [{ id: "markdown", extensions: [".md"] }] },
  modelUrl: () => "fixture.onnx",
  sha256: "fixture",
  contextBytes: 512,
  schema: fixture.schema,
  modifierThreshold: 0.6,
  structuredDecoder: fixture.parameters,
  decoder: { modifierRoles: { strong: ["text"] } },
};

describe("joint BIO decoder", () => {
  it("shares the native Unicode boundary, role and modifier oracle across committed windows", () => {
    const decoder = new StructuredSpanDecoder(model);
    const { units } = characterMap(fixture.source);
    for (let i = 0; i < units.length - 1; i++)
      decoder.append(
        units[i],
        units[i + 1],
        Float32Array.from(fixture.boundary[i]),
        0,
        Float32Array.from(fixture.token[i]),
        0,
        Float32Array.from(fixture.modifier[i]),
        0,
      );
    expect(decoder.finish()).toEqual(fixture.expected);
    expect(decoder.finish()).toEqual(fixture.expected);
    expect(new StructuredSpanDecoder(model).finish()).toEqual({
      offsetEncoding: "utf-16",
      spans: [],
    });
  });
  it("rejects mismatched roles, illegal I transitions and nonfinite weights", () => {
    for (const change of ["roles", "inside", "initial", "weight", "dimension"]) {
      const parameters = structuredClone(fixture.parameters);
      if (change === "roles") parameters.tokenTypes.reverse();
      if (change === "inside") parameters.transitions[0][2] = -1;
      if (change === "initial") parameters.initial[2] = -1;
      if (change === "weight") parameters.typeWeight = NaN;
      if (change === "dimension") parameters.transitions.pop();
      expect(
        () => new StructuredSpanDecoder({ ...model, structuredDecoder: parameters }),
      ).toThrow();
    }
  });
});
