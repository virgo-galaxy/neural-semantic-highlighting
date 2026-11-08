import "@nsh/highlighter/theme.css";
import "./style.css";

import { createHighlighter } from "@nsh/highlighter";

const highlighter = createHighlighter();
const source = document.querySelector("#source");
const language = document.querySelector("#language");
const preview = document.querySelector("#preview");
const status = document.querySelector("#status");
const themeButton = document.querySelector("#theme");
let revision = 0;

function showPlainCode() {
  const pre = document.createElement("pre");
  pre.className = "nsh";
  pre.dataset.language = language.value;
  const code = document.createElement("code");
  code.textContent = source.value;
  pre.append(code);
  preview.replaceChildren(pre);
}

function invalidate() {
  revision += 1;
  showPlainCode();
  preview.setAttribute("aria-busy", "false");
  status.textContent = "Ready to highlight";
}

async function highlight() {
  const request = ++revision;
  showPlainCode();
  preview.setAttribute("aria-busy", "true");
  status.textContent = "Highlighting…";
  try {
    const { html } = await highlighter.highlight(source.value, { language: language.value });
    if (request !== revision) return;
    preview.innerHTML = html; // Escaped by the NSH renderer.
    status.textContent = "Highlighted";
  } catch (reason) {
    if (request !== revision) return;
    status.textContent = `Unable to highlight: ${String(reason)}`;
  } finally {
    if (request === revision) preview.setAttribute("aria-busy", "false");
  }
}

source.addEventListener("input", invalidate);
language.addEventListener("change", invalidate);
document.querySelector("#highlight").addEventListener("click", () => {
  void highlight();
});
themeButton.addEventListener("click", () => {
  const dark = document.documentElement.dataset.nshTheme !== "dark";
  document.documentElement.dataset.nshTheme = dark ? "dark" : "light";
  themeButton.textContent = dark ? "Switch to light" : "Switch to dark";
});

// Release the worker when leaving; restart normally if restored from back/forward cache.
window.addEventListener("pagehide", (event) => {
  if (!event.persisted) highlighter.close();
});
void highlight();
