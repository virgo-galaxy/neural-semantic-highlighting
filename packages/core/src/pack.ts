import type { PackManifest } from "./manifest.js";
import type { HighlightResult } from "./result.js";

export interface HighlightRequest {
  source: string;
  documentKind: string;
}

export interface SemanticPack {
  /**
   * Metadata describing this pack and its supported document kinds.
   */
  manifest: PackManifest;

  /**
   * Analyze a source document and return semantic spans.
   */
  highlight(request: HighlightRequest): Promise<HighlightResult>;
}
