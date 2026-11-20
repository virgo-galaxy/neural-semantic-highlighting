import "@nsh/highlighter/theme.css";

import { createHighlighter } from "@nsh/highlighter";
import css from "@nsh/models/languages/css";
import typescript from "@nsh/models/languages/typescript";

// One worker and model cache for the whole client application.
export const highlighter = createHighlighter({ languages: [typescript, css] });
