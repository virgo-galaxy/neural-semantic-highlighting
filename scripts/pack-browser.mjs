import { spawnSync } from "node:child_process";
import {
  cpSync,
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { dirname, relative, resolve, sep } from "node:path";
import { parseArgs } from "node:util";

import ts from "typescript";

const { values } = parseArgs({
  options: { destination: { type: "string" }, "workspace-packages": { type: "boolean" } },
});
const workspacePackages = values["workspace-packages"];
const destination = resolve(
  values.destination ??
    (workspacePackages ? "artifacts/browser/npm" : "artifacts/browser/npm-release"),
);
const internalDirectories = [
  "packages/core",
  "packages/renderers/html",
  "packages/runtimes/browser",
];
const directories = [
  ...internalDirectories,
  "packages/highlighter",
  ...(workspacePackages ? ["packages/models"] : []),
];
const packages = directories.map((directory) => ({
  directory: resolve(directory),
  manifest: JSON.parse(readFileSync(resolve(directory, "package.json"), "utf8")),
}));

function prepareStaging(name) {
  const staging = resolve(destination, "staging", name);
  rmSync(staging, { recursive: true, force: true });
  mkdirSync(staging, { recursive: true });
  return staging;
}

function pack(staging, manifest) {
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
  if (result.status !== 0) throw result.error ?? new Error(result.stderr || result.stdout);
  const [archive] = JSON.parse(result.stdout);
  console.log(`${archive.name}: ${archive.filename} (${archive.size} bytes)`);
  return archive;
}

function packWorkspace() {
  const versions = new Map(packages.map(({ manifest }) => [manifest.name, manifest.version]));
  return packages.map(({ directory, manifest: original }) => {
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
    const staging = prepareStaging(manifest.name.replace("@nsh/", ""));
    cpSync(resolve(directory, "dist"), resolve(staging, "dist"), { recursive: true });
    if (existsSync(resolve(directory, "README.md")))
      cpSync(resolve(directory, "README.md"), resolve(staging, "README.md"));
    return pack(staging, manifest);
  });
}

function rewriteImports(file, entrypoints) {
  const source = readFileSync(file, "utf8");
  const tree = ts.createSourceFile(file, source, ts.ScriptTarget.Latest, true);
  const edits = [];
  function visit(node) {
    let specifier;
    if (ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) {
      specifier = node.moduleSpecifier;
    } else if (ts.isImportTypeNode(node) && ts.isLiteralTypeNode(node.argument)) {
      specifier = node.argument.literal;
    } else if (ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword) {
      specifier = node.arguments[0];
    }
    if (specifier && ts.isStringLiteral(specifier) && specifier.text.startsWith("@nsh/")) {
      const target = entrypoints.get(specifier.text);
      if (!target) throw new Error(`Missing internal export ${specifier.text} in ${file}`);
      const path = relative(dirname(file), target).split(sep).join("/");
      edits.push({
        start: specifier.getStart(tree),
        end: specifier.end,
        value: JSON.stringify(path.startsWith(".") ? path : `./${path}`),
      });
    }
    ts.forEachChild(node, visit);
  }
  visit(tree);
  if (edits.length === 0) return;
  let rewritten = source;
  for (const { start, end, value } of edits.reverse())
    rewritten = rewritten.slice(0, start) + value + rewritten.slice(end);
  writeFileSync(file, rewritten);
}

function packHighlighter() {
  const highlighter = packages.find(({ manifest }) => manifest.name === "@nsh/highlighter");
  const { description, version, type, exports, files, sideEffects } = highlighter.manifest;
  const { license } = JSON.parse(readFileSync(resolve("package.json"), "utf8"));
  const name = "neural-semantic-highlighting";
  const staging = prepareStaging(name);
  const dist = resolve(staging, "dist");
  const workspaceOnly = ["languages", "bundled.js", "bundled.d.ts"];
  const highlighterDist = resolve(highlighter.directory, "dist");
  cpSync(highlighterDist, dist, {
    recursive: true,
    filter: (file) => !workspaceOnly.includes(relative(highlighterDist, file)),
  });
  cpSync(resolve(highlighter.directory, "README.npm.md"), resolve(staging, "README.md"));
  cpSync(resolve("LICENSE"), resolve(staging, "LICENSE"));

  const entrypoints = new Map();
  const dependencies = {};
  for (const { directory, manifest } of packages) {
    if (manifest !== highlighter.manifest) {
      const internal = resolve(dist, "internal", manifest.name.replace("@nsh/", ""));
      cpSync(resolve(directory, "dist"), internal, { recursive: true });
      for (const [subpath, entry] of Object.entries(manifest.exports)) {
        const specifier = manifest.name + subpath.slice(1);
        entrypoints.set(specifier, resolve(internal, relative("dist", entry.import)));
      }
    }
    for (const [dependency, range] of Object.entries(manifest.dependencies ?? {})) {
      if (range.startsWith("workspace:")) continue;
      if (dependencies[dependency] && dependencies[dependency] !== range)
        throw new Error(`Conflicting versions for ${dependency}`);
      dependencies[dependency] = range;
    }
  }
  for (const file of readdirSync(dist, { recursive: true })) {
    if (file.endsWith(".js") || file.endsWith(".d.ts"))
      rewriteImports(resolve(dist, file), entrypoints);
  }
  const publicExports = { ...exports };
  delete publicExports["./languages/*"];
  delete publicExports["./bundled"];
  return pack(staging, {
    name,
    version,
    description,
    license,
    private: true,
    type,
    exports: publicExports,
    files,
    sideEffects,
    dependencies,
  });
}

const archives = workspacePackages ? packWorkspace() : [packHighlighter()];
writeFileSync(resolve(destination, "archives.json"), JSON.stringify(archives, null, 2) + "\n");
