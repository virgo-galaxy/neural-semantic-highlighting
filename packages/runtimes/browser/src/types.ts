import type { PackManifest } from "@nsh/core";

export interface StructuredDecoder {
  format: "nsh-joint-bio-v1";
  tokenTypes: readonly string[];
  typeWeight: number;
  transitionWeight: number;
  transitions: readonly (readonly (number | null)[])[];
  initial: readonly (number | null)[];
}

export interface WindowingPolicy {
  format: "nsh-overlap-logits-v1";
  strideBytes: 128 | 256;
  edgeWeightCap: 128;
  adaptiveWeight: 0 | 0.5;
}

export interface BrowserModel {
  id: string;
  dependencies?: readonly BrowserModel[];
  manifest: PackManifest;
  modelUrl(): string;
  sha256: string;
  contextBytes: number;
  schema: { tokenTypes: readonly string[]; modifiers: readonly string[] };
  modifierThreshold: number;
  structuredDecoder?: StructuredDecoder;
  inferenceWindowing?: WindowingPolicy;
  decoder?: {
    coalesceAdjacentTokenTypes?: readonly string[];
    modifierRoles?: Readonly<Record<string, readonly string[]>>;
  };
}

export interface ModelRequest extends Omit<BrowserModel, "modelUrl" | "dependencies"> {
  modelUrl: string;
}
