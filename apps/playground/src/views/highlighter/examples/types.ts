import type { ContentCategory } from "@nsh/highlighter/catalog";

export interface HighlighterContentType {
  id: string;
  label: string;
  category: ContentCategory;
  icon?: string;
}

export interface HighlighterExample {
  id: string;
  contentTypeId: string;
  filename: string;
  documentKind: string;
  source: string;
}
