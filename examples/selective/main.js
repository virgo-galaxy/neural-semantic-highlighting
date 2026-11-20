import "@nsh/highlighter/theme.css";

import { createHighlighter } from "@nsh/highlighter";
import css from "@nsh/models/languages/css";
import typescript from "@nsh/models/languages/typescript";

const highlighter = createHighlighter({ languages: [typescript, css] });
const checks = [];
try {
  for (const [language, source] of [
    ["tsx", 'export const App = () => <button className="action">Hello</button>;'],
    ["scss", ".root { display: grid; .action { color: #09f; &:hover { opacity: .8; } } }"],
  ]) {
    const output = await highlighter.highlight(source, { language });
    const block = document.createElement("div");
    block.innerHTML = output.html;
    document.querySelector("#preview").append(block);
    checks.push({
      language,
      sourcePreserved: block.textContent === source,
      spans: output.result.spans.length,
    });
  }
  const passed = checks.every((check) => check.sourcePreserved && check.spans > 0);
  document.querySelector("#status").textContent = passed ? "Completed" : "Failed";
  document.querySelector("#report").textContent = JSON.stringify({ passed, checks }, null, 2);
} catch (error) {
  document.querySelector("#status").textContent = "Failed";
  document.querySelector("#report").textContent = String(error);
} finally {
  highlighter.close();
}
