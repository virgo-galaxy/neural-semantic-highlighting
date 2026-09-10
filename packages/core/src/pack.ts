import type { PackManifest } from "./manifest.js";
import type { HighlightResult } from "./result.js";

export interface HighlightRequest {
  source: string;
  documentKind: string;
}

/**
 * Runtime boundary between semantic inference and NSH consumers.
 *
 * A pack may run a model locally, inside the browser (for example through
 * WASM/WebGPU/ONNX), or behind a remote transport. Consumers depend only on
 * this contract and the returned HighlightResult.
 */
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
