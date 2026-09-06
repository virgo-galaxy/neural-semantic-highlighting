export interface SemanticTokenTypeSchema {
  id: string;
}

export interface SemanticTokenModifierSchema {
  id: string;
}

export interface PackSchema {
  tokenTypes: readonly SemanticTokenTypeSchema[];
  tokenModifiers: readonly SemanticTokenModifierSchema[];
}
