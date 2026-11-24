import { allModels } from "@nsh/models";

import {
  createHighlighter as createConfiguredHighlighter,
  type HighlighterOptions,
} from "./highlighter.js";

export type {
  BrowserHighlighter,
  HighlightedCode,
  HighlighterOptions,
  ObserveElementOptions,
} from "./highlighter.js";

/** Opt in to all local model assets. Requires the optional @nsh/models package. */
export function createHighlighter(options: HighlighterOptions = {}) {
  return createConfiguredHighlighter({ ...options, languages: options.languages ?? allModels });
}
