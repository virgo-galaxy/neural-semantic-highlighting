export {
  createHighlighter,
  type CreateHighlighterOptions,
  type Highlighter,
} from "./highlighter.js";
export { normalizeLanguageId } from "./language.js";
export type { DocumentKindManifest, PackManifest } from "./manifest.js";
export type { HighlightRequest, SemanticPack } from "./pack.js";
export { PackRegistry } from "./registry.js";
export type { HighlightResult, OffsetEncoding, SemanticSpan } from "./result.js";
export type { PackSchema, SemanticTokenModifierSchema, SemanticTokenTypeSchema } from "./schema.js";
