import "@virgo-design/fonts/sans/inter.css";
import "@virgo-design/fonts/mono/jetbrains-mono.css";
import "@virgo-design/tokens/styles.css";
import "@virgo-design/themes/virgo.css";
import "@virgo-design/ui/styles.css";
import "@nsh/highlighter/themes.css";
import "@/styles/playground.scss";

import { createRoot } from "react-dom/client";

import { Playground } from "@/views/highlighter/Playground";

createRoot(document.getElementById("app")!).render(<Playground />);
