export interface HighlighterLanguage {
  id: string;
  label: string;
  icon?: string;
}

export interface HighlighterExample {
  id: string;
  languageId: string;
  filename: string;
  documentKind: string;
  source: string;
}
