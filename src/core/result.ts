export type OffsetEncoding = "utf-8" | "utf-16" | "utf-32";

export interface SemanticSpan {
  /**
   * Start offset in the source document.
   * Inclusive.
   */
  start: number;

  /**
   * End offset in the source document.
   * Exclusive.
   */
  end: number;

  /**
   * Semantic token type defined by the active pack.
   */
  tokenType: string;
}

export interface HighlightResult {
  /**
   * Encoding used to interpret span offsets.
   */
  offsetEncoding: OffsetEncoding;

  spans: SemanticSpan[];
}
