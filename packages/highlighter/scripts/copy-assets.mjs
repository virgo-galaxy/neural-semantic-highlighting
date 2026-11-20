import { copyFileSync, cpSync, mkdirSync } from "node:fs";
const root = new URL("../../../", import.meta.url);
const dist = new URL("../dist/", import.meta.url);
mkdirSync(dist, { recursive: true });
cpSync(new URL("packages/themes/web/dist/", root), new URL("themes/", dist), { recursive: true });
copyFileSync(new URL("packages/themes/web/dist/default.css", root), new URL("theme.css", dist));
