import { argmax } from "./decode.js";
import type { BrowserModel, WindowingPolicy } from "./types.js";

type Logits = readonly [ArrayLike<number>, ArrayLike<number>, ArrayLike<number>];
type RunWindow = (bytes: Uint8Array) => Promise<Logits>;

export function validateWindowing(policy: WindowingPolicy, context: number) {
  if (
    context !== 512 ||
    policy.format !== "nsh-overlap-logits-v1" ||
    ![128, 256].includes(policy.strideBytes) ||
    policy.edgeWeightCap !== 128 ||
    ![0, 0.5].includes(policy.adaptiveWeight)
  )
    throw new Error("Invalid neural window-fusion policy");
}

/** Fuse neural logits at original byte/character positions; no source grammar. */
export async function windowLogits(
  model: BrowserModel,
  raw: Uint8Array,
  starts: readonly number[],
  run: RunWindow,
): Promise<readonly Float64Array[]> {
  const policy = model.inferenceWindowing!;
  validateWindowing(policy, model.contextBytes);
  const widths = [3, model.schema.tokenTypes.length, model.schema.modifiers.length];
  const count = starts.length - 1;
  const values = widths.map((width) => new Float64Array(count * width));
  const counts = new Float64Array(count);
  let begin = 0;
  while (begin < count) {
    let end = begin + 1;
    while (end + 1 < starts.length && starts[end + 1] <= starts[begin] + model.contextBytes) end++;
    const output = await run(raw.subarray(starts[begin], starts[end]));
    for (let i = begin; i < end; i++) {
      const offset = starts[i] - starts[begin];
      const weight = Math.min(offset + 1, starts[end] - starts[i], policy.edgeWeightCap);
      counts[i] += weight;
      for (let head = 0; head < widths.length; head++)
        for (let column = 0; column < widths[head]; column++)
          values[head][i * widths[head] + column] +=
            output[head][offset * widths[head] + column] * weight;
    }
    if (end === count) break;
    const limit = starts[begin] + policy.strideBytes;
    let next = begin;
    while (next + 1 < starts.length && starts[next + 1] <= limit) next++;
    if (next <= begin) throw new Error("Overlapping inference cursor made no progress");
    begin = next;
  }
  for (let i = 0; i < count; i++)
    for (let head = 0; head < widths.length; head++)
      for (let column = 0; column < widths[head]; column++)
        values[head][i * widths[head] + column] =
          (values[head][i * widths[head] + column] / counts[i]) * (1 - policy.adaptiveWeight);
  if (policy.adaptiveWeight) {
    begin = 0;
    while (begin < count) {
      let end = begin + 1;
      while (end + 1 < starts.length && starts[end + 1] <= starts[begin] + model.contextBytes)
        end++;
      const output = await run(raw.subarray(starts[begin], starts[end]));
      let commit = end === count ? end : end - 1;
      if (end < count && argmax(output[0], (starts[commit] - starts[begin]) * 3, 3) === 2) {
        for (let i = commit - 1; i >= begin; i--) {
          const label = argmax(output[0], (starts[i] - starts[begin]) * 3, 3);
          if (label === 1) {
            if (i > begin) commit = i;
            break;
          }
          if (label !== 2) break;
        }
      }
      if (commit <= begin) throw new Error("Browser inference cursor made no progress");
      for (let i = begin; i < commit; i++) {
        const offset = starts[i] - starts[begin];
        for (let head = 0; head < widths.length; head++)
          for (let column = 0; column < widths[head]; column++)
            values[head][i * widths[head] + column] +=
              output[head][offset * widths[head] + column] * policy.adaptiveWeight;
      }
      begin = commit;
    }
  }
  return values;
}
