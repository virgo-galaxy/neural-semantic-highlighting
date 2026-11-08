import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
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
]) {
  copyFileSync(new URL(`packs/${id}/browser/model.onnx`, root), new URL(`models/${id}.onnx`, dist));
}
writeFileSync(
  new URL("theme.css", dist),
  readFileSync(new URL("packages/themes/web/base.css", root), "utf8") +
    "\n" +
    readFileSync(new URL("packages/themes/web/languages/typescript.css", root), "utf8"),
);
