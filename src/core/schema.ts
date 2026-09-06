export interface SemanticTokenTypeSchema {
  id: string;
}

export interface PackSchema {
  tokenTypes: readonly SemanticTokenTypeSchema[];
}
