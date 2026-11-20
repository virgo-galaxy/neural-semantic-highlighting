import { mkdirSync } from "node:fs";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";

const destination = resolve("artifacts/browser/npm");
mkdirSync(destination, { recursive: true });
for (const name of ["core", "html", "browser", "highlighter", "models"]) {
  const result = spawnSync(
    "pnpm",
    ["--filter", `@nsh/${name}`, "pack", "--pack-destination", destination],
    { stdio: "inherit" },
  );
  if (result.status !== 0) process.exit(result.status ?? 1);
}
