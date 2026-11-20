import { cpSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { parseArgs } from "node:util";

const { values } = parseArgs({ options: { destination: { type: "string" } } });
const destination = resolve(values.destination ?? "artifacts/browser/npm");
mkdirSync(destination, { recursive: true });
const directories = [
  "packages/core",
  "packages/renderers/html",
  "packages/runtimes/browser",
  "packages/highlighter",
  "packages/models",
];
const packages = directories.map((directory) => ({
  directory: resolve(directory),
  manifest: JSON.parse(readFileSync(resolve(directory, "package.json"), "utf8")),
}));
const versions = new Map(packages.map(({ manifest }) => [manifest.name, manifest.version]));
const archives = [];
for (const { directory, manifest: original } of packages) {
  const manifest = structuredClone(original);
  for (const field of ["dependencies", "peerDependencies", "optionalDependencies"]) {
    for (const [name, version] of Object.entries(manifest[field] ?? {})) {
      if (!version.startsWith("workspace:")) continue;
      if (!versions.has(name)) throw new Error(`Unknown packed workspace dependency: ${name}`);
      manifest[field][name] = versions.get(name);
    }
  }
  delete manifest.devDependencies;
  delete manifest.scripts;
  const staging = resolve(destination, "staging", manifest.name.replace("@nsh/", ""));
  rmSync(staging, { recursive: true, force: true });
  mkdirSync(staging, { recursive: true });
  cpSync(resolve(directory, "dist"), resolve(staging, "dist"), { recursive: true });
  if (existsSync(resolve(directory, "README.md")))
    cpSync(resolve(directory, "README.md"), resolve(staging, "README.md"));
  writeFileSync(resolve(staging, "package.json"), JSON.stringify(manifest, null, 2) + "\n");
  const result = spawnSync(
    "npm",
    [
      "pack",
      "--offline",
      "--ignore-scripts",
      "--json",
      "--pack-destination",
      destination,
      "--cache",
      resolve(destination, ".npm-cache"),
    ],
    { cwd: staging, encoding: "utf8" },
  );
  if (result.status !== 0) throw new Error(result.stderr || result.stdout);
  const [archive] = JSON.parse(result.stdout);
  archives.push(archive);
  console.log(`${archive.name}: ${archive.filename} (${archive.size} bytes)`);
}
writeFileSync(resolve(destination, "archives.json"), JSON.stringify(archives, null, 2) + "\n");
