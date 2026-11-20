import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import {
  cpSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { pathToFileURL } from "node:url";
import { parseArgs } from "node:util";

const { values } = parseArgs({
  options: {
    archives: { type: "string", default: "artifacts/browser/npm" },
    output: { type: "string", default: "artifacts/browser/delivery-check" },
    "seed-node-modules": { type: "string" },
    offline: { type: "boolean", default: false },
  },
});
const output = resolve(values.output);
const archives = JSON.parse(readFileSync(resolve(values.archives, "archives.json"), "utf8"));
const require = createRequire(new URL("../apps/playground/package.json", import.meta.url));
const { build } = await import(pathToFileURL(require.resolve("vite")).href);
const report = { packageModels: {}, consumers: {} };
for (const archive of archives) {
  const weights = archive.files.filter((file) => file.path.endsWith(".onnx"));
  report.packageModels[archive.name] = {
    models: weights.length,
    archiveBytes: archive.size,
    unpackedBytes: archive.unpackedSize,
  };
  assert.equal(weights.length, archive.name === "@nsh/models" ? 40 : 0);
}

for (const mode of ["local", "base"]) {
  // Outside the checkout: package resolution cannot fall back to workspace links.
  const folder = mkdtempSync(join(tmpdir(), `nsh-${mode}-`));
  const dependencies = Object.fromEntries(
    archives
      .filter((archive) => mode === "local" || archive.name !== "@nsh/models")
      .map((archive) => [archive.name, `file:${resolve(values.archives, archive.filename)}`]),
  );
  writeFileSync(
    join(folder, "package.json"),
    JSON.stringify({ private: true, type: "module", dependencies }),
  );
  const modules = join(folder, "node_modules");
  mkdirSync(modules, { recursive: true });
  if (values["seed-node-modules"]) {
    for (const name of readdirSync(values["seed-node-modules"])) {
      if (name.startsWith(".") || name === "@nsh") continue;
      cpSync(resolve(values["seed-node-modules"], name), join(modules, name), {
        recursive: true,
        dereference: true,
      });
    }
  }
  const installed = spawnSync(
    "npm",
    [
      "install",
      "--ignore-scripts",
      "--no-audit",
      "--no-fund",
      "--package-lock=false",
      "--cache",
      join(output, ".npm-cache"),
      ...(values.offline ? ["--offline"] : []),
    ],
    { cwd: folder, encoding: "utf8" },
  );
  if (installed.status !== 0) throw new Error(installed.stderr || installed.stdout);
  if (mode === "base") assert.equal(existsSync(join(modules, "@nsh/models")), false);
  if (mode === "local") {
    cpSync(resolve("examples/selective"), folder, { recursive: true });
  } else {
    writeFileSync(join(folder, "index.html"), '<script type="module" src="/main.js"></script>');
    writeFileSync(
      join(folder, "main.js"),
      'import { createHighlighter } from "@nsh/highlighter";\nglobalThis.nsh = { createHighlighter };\n',
    );
  }
  await build({
    configFile: false,
    root: folder,
    logLevel: "error",
    build: {
      target: "es2022",
      assetsInlineLimit: 0,
      outDir: "dist",
      emptyOutDir: true,
    },
  });
  const dist = join(folder, "dist");
  const files = readdirSync(dist, { recursive: true }).map(String);
  const models = files.filter((file) => file.endsWith(".onnx"));
  assert.equal(models.length, mode === "local" ? 2 : 0);
  assert.equal(files.filter((file) => file.endsWith(".wasm")).length, 1);
  if (mode === "local") {
    const hashes = models
      .map((file) =>
        createHash("sha256")
          .update(readFileSync(join(dist, file)))
          .digest("hex"),
      )
      .sort();
    const expected = ["typescript", "css"]
      .map((id) => JSON.parse(readFileSync(`packs/${id}/browser/model.json`, "utf8")).model.sha256)
      .sort();
    assert.deepEqual(hashes, expected);
  }
  mkdirSync(output, { recursive: true });
  rmSync(join(output, mode), { recursive: true, force: true });
  cpSync(dist, join(output, mode), { recursive: true });
  report.consumers[mode] = {
    onnx: models.length,
    wasm: 1,
    optionalModelsInstalled: existsSync(join(modules, "@nsh/models")),
    onnxBytes: models.reduce((sum, file) => sum + readFileSync(join(dist, file)).length, 0),
  };
  console.log(
    `${mode}: ${models.length} ONNX, one shared WASM; installed packages, no workspace links`,
  );
}
writeFileSync(join(output, "verification.json"), JSON.stringify(report, null, 2) + "\n");
