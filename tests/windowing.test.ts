import { describe, expect, it } from "vitest";

import { characterMap } from "../packages/runtimes/browser/src/decode.js";
import type { BrowserModel, WindowingPolicy } from "../packages/runtimes/browser/src/types.js";
import { validateWindowing, windowLogits } from "../packages/runtimes/browser/src/windowing.js";
import reference from "./fixtures/window-fusion.json";

describe("position-only neural window fusion", () => {
  it("matches native Unicode, CRLF and adaptive-cut reference logits", async () => {
    const { bytes: starts } = characterMap(reference.source);
    for (const row of reference.cases) {
      const model = {
        contextBytes: 512,
        schema: { tokenTypes: ["x", "y"], modifiers: ["flag"] },
        inferenceWindowing: row.policy,
      } as unknown as BrowserModel;
      const actual = await windowLogits(
        model,
        new TextEncoder().encode(reference.source),
        starts,
        async (bytes) => {
          const boundary: number[] = [],
            roles: number[] = [],
            modifiers: number[] = [];
          for (let i = 0; i < bytes.length; i++) {
            boundary.push((bytes[i] + i) % 11 === 0 ? 2 : 0, (bytes[i] + i) % 7 === 0 ? 3 : 0, 1);
            // Match float32 neural head arithmetic before float64 accumulation.
            roles.push(
              Math.fround((bytes[i] % 13) * Math.fround(0.1)),
              Math.fround((i % 17) * Math.fround(0.2)),
            );
            modifiers.push((bytes[i] % 5) * 0.25);
          }
          return [
            Float32Array.from(boundary),
            Float32Array.from(roles),
            Float32Array.from(modifiers),
          ];
        },
      );
      for (let head = 0; head < actual.length; head++) {
        expect(actual[head].length).toBe(row.expected[head].length);
        for (let i = 0; i < actual[head].length; i++)
          expect(actual[head][i]).toBeCloseTo(row.expected[head][i], 10);
      }
    }
  });
  it("rejects unsupported window policy values", () => {
    expect(() =>
      validateWindowing(
        {
          format: "nsh-overlap-logits-v1",
          strideBytes: 0,
          edgeWeightCap: 128,
          adaptiveWeight: 0,
        } as unknown as WindowingPolicy,
        512,
      ),
    ).toThrow();
  });
});
