import type { HighlightResult } from "@nsh/core";
import * as ort from "onnxruntime-web/wasm";

import { type BrowserRuntimeOptions, ModelAssetCache, runtimePolicy } from "./assets.js";
import { argmax, characterMap, SpanDecoder } from "./decode.js";
import { SessionPool } from "./sessions.js";
import { StructuredSpanDecoder } from "./structured.js";
import type { BrowserModel, ModelRequest } from "./types.js";
import { windowLogits } from "./windowing.js";

// One thread works without COOP/COEP or SharedArrayBuffer. Both files are shipped
// with this package and resolved by the consumer's bundler; no CDN dependency.
ort.env.wasm.numThreads = 1;
ort.env.wasm.wasmPaths = {
  wasm: new URL("./ort-wasm-simd-threaded.wasm", import.meta.url).href,
  mjs: new URL("./ort-wasm-simd-threaded.mjs", import.meta.url).href,
};

const sessions = new SessionPool<ort.InferenceSession>();

export async function highlight(
  model: ModelRequest,
  source: string,
  options: BrowserRuntimeOptions = {},
): Promise<HighlightResult> {
  const { bytes: starts, units } = characterMap(source);
  const decoder = model.structuredDecoder
    ? new StructuredSpanDecoder(model as unknown as BrowserModel)
    : new SpanDecoder(model as unknown as BrowserModel);
  if (!source.length) return decoder.finish();
  const raw = new TextEncoder().encode(source);
  const policy = runtimePolicy(options);
  return sessions.use(
    model.id + ":" + model.sha256,
    policy.maxLoadedModels,
    async () => {
      const bytes = await new ModelAssetCache(policy).load({
        modelId: model.id,
        kind: "model",
        sha256: model.sha256,
        url: () => model.modelUrl,
      });
      return ort.InferenceSession.create(bytes, { executionProviders: ["wasm"] });
    },
    async (session) => {
      if (model.inferenceWindowing && raw.length > model.contextBytes) {
        const values = await windowLogits(
          model as unknown as BrowserModel,
          raw,
          starts,
          async (bytes) => {
            const input = new ort.Tensor(
              "int64",
              BigInt64Array.from(bytes, (value) => BigInt(value)),
              [1, bytes.length],
            );
            let output: Awaited<ReturnType<typeof session.run>> | undefined;
            try {
              output = await session.run({ input_ids: input });
              return [
                (output.boundary.data as Float32Array).slice(),
                (output.token_type.data as Float32Array).slice(),
                (output.modifier.data as Float32Array).slice(),
              ];
            } finally {
              input.dispose();
              for (const value of Object.values(output ?? {})) value.dispose();
            }
          },
        );
        for (let i = 0; i < starts.length - 1; i++) {
          if (decoder instanceof StructuredSpanDecoder)
            decoder.append(
              units[i],
              units[i + 1],
              values[0],
              i * 3,
              values[1],
              i * model.schema.tokenTypes.length,
              values[2],
              i * model.schema.modifiers.length,
            );
          else
            decoder.append(
              units[i],
              units[i + 1],
              argmax(values[0], i * 3, 3),
              values[1],
              i * model.schema.tokenTypes.length,
              values[2],
              i * model.schema.modifiers.length,
            );
        }
        return decoder.finish();
      }
      let cursorIndex = 0;
      while (cursorIndex < starts.length - 1) {
        const cursor = starts[cursorIndex];
        const limit = Math.min(cursor + model.contextBytes, raw.length);
        let endIndex = cursorIndex + 1;
        while (endIndex + 1 < starts.length && starts[endIndex + 1] <= limit) endIndex++;
        const end = starts[endIndex];
        const ids = BigInt64Array.from(raw.subarray(cursor, end), (value) => BigInt(value));
        const input = new ort.Tensor("int64", ids, [1, ids.length]);
        let output: Awaited<ReturnType<typeof session.run>> | undefined;
        try {
          output = await session.run({ input_ids: input });
          const boundary = output.boundary.data as Float32Array;
          const type = output.token_type.data as Float32Array;
          const modifier = output.modifier.data as Float32Array;
          let commitIndex = end === raw.length ? endIndex : endIndex - 1;
          if (end < raw.length && argmax(boundary, (starts[commitIndex] - cursor) * 3, 3) === 2) {
            for (let i = commitIndex - 1; i >= cursorIndex; i--) {
              const label = argmax(boundary, (starts[i] - cursor) * 3, 3);
              if (label === 1) {
                if (i > cursorIndex) commitIndex = i;
                break;
              }
              if (label !== 2) break;
            }
          }
          if (commitIndex <= cursorIndex)
            throw new Error("Browser inference cursor made no progress");
          for (let i = cursorIndex; i < commitIndex; i++) {
            const offset = starts[i] - cursor;
            if (decoder instanceof StructuredSpanDecoder)
              decoder.append(
                units[i],
                units[i + 1],
                boundary,
                offset * 3,
                type,
                offset * model.schema.tokenTypes.length,
                modifier,
                offset * model.schema.modifiers.length,
              );
            else
              decoder.append(
                units[i],
                units[i + 1],
                argmax(boundary, offset * 3, 3),
                type,
                offset * model.schema.tokenTypes.length,
                modifier,
                offset * model.schema.modifiers.length,
              );
          }
          cursorIndex = commitIndex;
        } finally {
          input.dispose();
          for (const value of Object.values(output ?? {})) value.dispose();
        }
      }
      return decoder.finish();
    },
  );
}
