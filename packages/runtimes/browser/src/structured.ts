import type { HighlightResult } from "@nsh/core";

import { argmax, SpanDecoder } from "./decode.js";
import type { BrowserModel, StructuredDecoder } from "./types.js";

function validate(parameters: StructuredDecoder, model: BrowserModel) {
  const states = 1 + model.schema.tokenTypes.length * 2;
  const score = (value: unknown) =>
    typeof value === "number" && Number.isFinite(value) && value <= 0;
  if (
    parameters.format !== "nsh-joint-bio-v1" ||
    JSON.stringify(parameters.tokenTypes) !== JSON.stringify(model.schema.tokenTypes) ||
    ![parameters.typeWeight, parameters.transitionWeight].every(
      (value) => Number.isFinite(value) && value > 0,
    ) ||
    parameters.initial.length !== states ||
    parameters.transitions.length !== states ||
    parameters.transitions.some((row) => row.length !== states)
  )
    throw new Error("Invalid structured decoder configuration");
  for (let a = 0; a < states; a++) {
    if (a > 0 && a % 2 === 0 ? parameters.initial[a] !== null : !score(parameters.initial[a]))
      throw new Error("Invalid structured decoder initial state");
    for (let b = 0; b < states; b++) {
      const legal = b === 0 || b % 2 === 1 || a === b || a === b - 1;
      if (legal ? !score(parameters.transitions[a][b]) : parameters.transitions[a][b] !== null)
        throw new Error("Invalid structured decoder transition");
    }
  }
}

/** Joint BIO/role Viterbi over committed neural character logits. Source-blind. */
export class StructuredSpanDecoder {
  readonly #model: BrowserModel;
  readonly #parameters: StructuredDecoder;
  readonly #back: Uint16Array[] = [];
  readonly #starts: number[] = [];
  readonly #ends: number[] = [];
  readonly #modifiers: Float64Array[] = [];
  #scores: Float64Array;

  constructor(model: BrowserModel) {
    if (!model.structuredDecoder) throw new Error("Missing structured decoder");
    validate(model.structuredDecoder, model);
    this.#model = model;
    this.#parameters = model.structuredDecoder;
    this.#scores = new Float64Array(this.#parameters.initial.length);
  }

  append(
    start: number,
    end: number,
    boundary: ArrayLike<number>,
    boundaryOffset: number,
    types: ArrayLike<number>,
    typeOffset: number,
    modifiers: ArrayLike<number>,
    modifierOffset: number,
  ) {
    const { typeWeight, transitionWeight, initial, transitions } = this.#parameters;
    const roles = this.#model.schema.tokenTypes.length;
    const maximum = types[typeOffset + argmax(types, typeOffset, roles)];
    const scores = new Float64Array(this.#scores.length);
    const back = new Uint16Array(scores.length);
    for (let state = 0; state < scores.length; state++) {
      let best = initial[state] === null ? -Infinity : initial[state]! * transitionWeight;
      if (this.#back.length) {
        best = -Infinity;
        for (let previous = 0; previous < scores.length; previous++) {
          const transition = transitions[previous][state];
          if (transition === null) continue;
          const value = this.#scores[previous] + transitionWeight * transition;
          if (value > best) {
            best = value;
            back[state] = previous;
          }
        }
      }
      const label = state === 0 ? 0 : state % 2 === 1 ? 1 : 2;
      const type =
        state === 0 ? 0 : typeWeight * (types[typeOffset + Math.floor((state - 1) / 2)] - maximum);
      scores[state] = best + (boundary[boundaryOffset + label] + type);
    }
    this.#scores = scores;
    this.#back.push(back);
    this.#starts.push(start);
    this.#ends.push(end);
    this.#modifiers.push(
      Float64Array.from(this.#model.schema.modifiers, (_, i) => modifiers[modifierOffset + i]),
    );
  }

  finish(): HighlightResult {
    const decoder = new SpanDecoder(this.#model);
    const path = new Uint16Array(this.#back.length);
    let state = argmax(this.#scores, 0, this.#scores.length);
    for (let index = path.length - 1; index >= 0; index--) {
      path[index] = state;
      state = this.#back[index][state];
    }
    const types = new Float64Array(this.#model.schema.tokenTypes.length);
    for (let index = 0; index < path.length; index++) {
      const value = path[index];
      types.fill(0);
      if (value) types[Math.floor((value - 1) / 2)] = 1;
      decoder.append(
        this.#starts[index],
        this.#ends[index],
        value === 0 ? 0 : value % 2 === 1 ? 1 : 2,
        types,
        0,
        this.#modifiers[index],
        0,
      );
    }
    return decoder.finish();
  }
}
