import "@nsh/highlighter/theme.css";

import { createHighlighter } from "@nsh/highlighter";

// Serve exported assets at /models/ or use the full storage URL.
export const highlighter = createHighlighter({
  modelBaseUrl: "/models/",
  languages: ["tsx", "scss"],
});
