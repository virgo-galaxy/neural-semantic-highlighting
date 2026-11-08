import type { HighlightResult, SemanticSpan } from "@nsh/core";

import type { BrowserModel } from "./types.js";

/** Original UTF-8 starts and UTF-16 offsets; no source-language parsing. */
export function characterMap(source: string) {
  const bytes = [0];
  const units = [0];
  let byte = 0;
  let unit = 0;
  for (const character of source) {
    const point = character.codePointAt(0)!;
    if (point >= 0xd800 && point <= 0xdfff)
      throw new Error("Source contains an unpaired surrogate");
    byte += point <= 0x7f ? 1 : point <= 0x7ff ? 2 : point <= 0xffff ? 3 : 4;
    unit += character.length;
    bytes.push(byte);
    units.push(unit);
  }
  return { bytes, units };
}

export function argmax(data: ArrayLike<number>, offset: number, width: number) {
  let best = 0;
  for (let i = 1; i < width; i++) if (data[offset + i] > data[offset + best]) best = i;
  return best;
}

/** Stream committed model windows; retain only one pending span's logits. */
export class SpanDecoder {
  readonly spans: SemanticSpan[] = [];
  readonly #model: BrowserModel;
  #start: number | undefined;
  #end = 0;
  #types: Float64Array;
  #flags: boolean[] = [];

  constructor(model: BrowserModel) {
    this.#model = model;
    this.#types = new Float64Array(model.schema.tokenTypes.length);
  }

  append(
    start: number,
    end: number,
    boundary: number,
    types: ArrayLike<number>,
    typeOffset: number,
    modifiers: ArrayLike<number>,
    modifierOffset: number,
  ) {
    if (boundary === 0 || boundary === 1) this.#flush();
    if (boundary === 0) return;
    if (this.#start === undefined) {
      this.#start = start;
      this.#flags = this.#model.schema.modifiers.map(
        (_, i) =>
          1 / (1 + Math.exp(-modifiers[modifierOffset + i])) >= this.#model.modifierThreshold,
      );
    }
    this.#end = end;
    for (let i = 0; i < this.#types.length; i++) this.#types[i] += types[typeOffset + i];
  }

  #flush() {
    if (this.#start === undefined) return;
    const tokenType = this.#model.schema.tokenTypes[argmax(this.#types, 0, this.#types.length)];
    const span: SemanticSpan = { start: this.#start, end: this.#end, tokenType };
    const roles = this.#model.decoder?.modifierRoles;
    const modifiers = this.#model.schema.modifiers.filter(
      (name, i) => this.#flags[i] && (!roles?.[name] || roles[name].includes(tokenType)),
    );
    if (modifiers.length) span.modifiers = modifiers;
    const previous = this.spans.at(-1);
    if (
      previous &&
      this.#model.decoder?.coalesceAdjacentTokenTypes?.includes(tokenType) &&
      previous.tokenType === tokenType &&
      previous.end === span.start &&
      (previous.modifiers ?? []).join(" ") === modifiers.join(" ")
    )
      previous.end = span.end;
    else this.spans.push(span);
    this.#start = undefined;
    this.#types.fill(0);
  }

  finish(): HighlightResult {
    this.#flush();
    return { offsetEncoding: "utf-16", spans: this.spans };
  }
}
