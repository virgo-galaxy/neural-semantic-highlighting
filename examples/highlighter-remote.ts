import "neural-semantic-highlighting/theme.css";

import { createHighlighter } from "neural-semantic-highlighting";

// Serve exported assets at /models/ or use the full storage URL.
export const highlighter = createHighlighter({
  modelBaseUrl: "/models/",
  languages: ["tsx", "scss"],
});
