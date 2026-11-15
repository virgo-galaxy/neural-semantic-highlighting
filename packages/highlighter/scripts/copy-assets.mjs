import { copyFileSync, cpSync, mkdirSync } from "node:fs";
const root = new URL("../../../", import.meta.url);
const dist = new URL("../dist/", import.meta.url);
mkdirSync(new URL("models/", dist), { recursive: true });
for (const id of [
  "typescript",
  "go",
  "css",
  "html",
  "vue",
  "python",
  "bash",
  "perl",
  "awk",
  "sql",
  "powershell",
  "bat",
  "assembly",
  "java",
  "csharp",
  "c",
  "cpp",
  "php",
  "svelte",
  "rust",
  "zig",
  "dart",
  "swift",
  "kotlin",
  "r",
  "scala",
  "ruby",
  "lua",
  "json",
  "yaml",
  "toml",
  "ini",
]) {
  copyFileSync(new URL(`packs/${id}/browser/model.onnx`, root), new URL(`models/${id}.onnx`, dist));
}
cpSync(new URL("packages/themes/web/dist/", root), new URL("themes/", dist), { recursive: true });
copyFileSync(new URL("packages/themes/web/dist/default.css", root), new URL("theme.css", dist));
