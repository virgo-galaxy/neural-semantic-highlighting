import type { PackManifest } from "@nsh/core";

export interface BrowserModel {
  id: string;
  dependencies?: readonly BrowserModel[];
  manifest: PackManifest;
  modelUrl(): string;
  sha256: string;
  contextBytes: number;
  schema: { tokenTypes: readonly string[]; modifiers: readonly string[] };
  modifierThreshold: number;
  decoder?: {
    coalesceAdjacentTokenTypes?: readonly string[];
    modifierRoles?: Readonly<Record<string, readonly string[]>>;
  };
}

export interface ModelRequest extends Omit<BrowserModel, "modelUrl" | "dependencies"> {
  modelUrl: string;
}
