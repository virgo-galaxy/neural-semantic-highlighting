import "@nsh/highlighter/theme.css";

import { createHighlighter } from "@nsh/highlighter";

// One worker and model cache for the whole client application.
export const highlighter = createHighlighter();
