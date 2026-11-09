import { mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { basename, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import Ajv from "ajv";

const packageRoot = fileURLToPath(new URL("../", import.meta.url));
const fields = ["color", "font-style", "font-weight", "text-decoration"];
const modes = ["light", "dark"];
const read = (path) => JSON.parse(readFileSync(path, "utf8"));

export function mergeStyle(base, patch = {}) {
  const asObject = (style) => (typeof style === "string" ? { color: style } : style);
  return { ...asObject(base), ...asObject(patch) };
}

function values(style) {
  return {
    color: style.color,
    "font-style": style.italic ? "italic" : "normal",
    "font-weight": style.bold ? "bold" : "normal",
    "text-decoration":
      [style.underline && "underline", style.strikethrough && "line-through"]
        .filter(Boolean)
        .join(" ") || "none",
  };
}

export function loadThemes(source = join(packageRoot, "src")) {
  const schema = read(join(source, "schema.json"));
  const ajv = new Ajv({ allErrors: true, strict: true, ownProperties: true });
  ajv.addSchema(schema);
  const validate = (type, value, path) => {
    if (!ajv.getSchema(`urn:nsh:theme#/definitions/${type}`)(value))
      throw new Error(
        `${path}: ${ajv.errorsText(ajv.getSchema(`urn:nsh:theme#/definitions/${type}`).errors)}`,
      );
  };
  const roles = schema.definitions.tokens.required;
  const families = new Map();
  const themes = readdirSync(join(source, "themes"), { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .sort((a, b) => a.name.localeCompare(b.name))
    .map((entry) => {
      const folder = join(source, "themes", entry.name);
      const metadata = read(join(folder, "theme.json"));
      validate("metadata", metadata, join(folder, "theme.json"));
      if (metadata.id !== entry.name)
        throw new Error(`Theme ID must match its directory: ${entry.name}`);
      const palettes = Object.fromEntries(
        modes.map((mode) => {
          const path = join(folder, `${mode}.json`),
            data = read(path);
          validate("palette", data, path);
          return [mode, data];
        }),
      );
      const languages = Object.create(null);
      const kinds = new Set();
      for (const file of readdirSync(join(folder, "languages")).sort()) {
        if (!file.endsWith(".json")) continue;
        const id = basename(file, ".json");
        if (!/^[a-z][a-z0-9-]*$/.test(id)) throw new Error(`Invalid language family: ${file}`);
        const path = join(folder, "languages", file),
          data = read(path);
        validate("language", data, path);
        const known = families.get(id);
        if (known && JSON.stringify(known.documentKinds) !== JSON.stringify(data.documentKinds))
          throw new Error(`Inconsistent document kinds for language family: ${id}`);
        for (const kind of data.documentKinds) {
          if (kinds.has(kind))
            throw new Error(`Duplicate document kind in ${metadata.id}: ${kind}`);
          kinds.add(kind);
        }
        const patchedRoles = new Set([
          ...(known?.roles ?? []),
          ...modes.flatMap((mode) => Object.keys(data[mode].tokens)),
        ]);
        families.set(id, { documentKinds: data.documentKinds, roles: [...patchedRoles].sort() });
        languages[id] = data;
      }
      return { ...metadata, palettes, languages };
    });
  if (!themes.some((theme) => theme.id === "default"))
    throw new Error("A complete default theme is required");
  themes.sort((a, b) =>
    a.id === "default"
      ? -1
      : b.id === "default"
        ? 1
        : (a.order ?? 100) - (b.order ?? 100) || a.id.localeCompare(b.id),
  );
  return { themes, roles, families, baseCss: readFileSync(join(source, "base.css"), "utf8") };
}

export function resolveStyles(theme, mode, families) {
  const palette = theme.palettes[mode];
  const result = {
    background: palette.background,
    foreground: palette.foreground,
    "selection-background": palette.selectionBackground,
    "selection-foreground": palette.selectionForeground,
  };
  for (const [role, style] of Object.entries(palette.tokens))
    for (const [field, value] of Object.entries(values(mergeStyle(style))))
      result[`${role}-${field}`] = value;
  for (const [family, config] of families)
    for (const role of config.roles)
      for (const [field, value] of Object.entries(
        values(
          mergeStyle(
            palette.tokens[role],
            Object.hasOwn(theme.languages[family]?.[mode].tokens ?? {}, role)
              ? theme.languages[family][mode].tokens[role]
              : undefined,
          ),
        ),
      ))
        result[`${family}-${role}-${field}`] = value;
  return result;
}

const block = (selector, declarations) =>
  `${selector} {\n${declarations.map(([key, value]) => `  ${key}: ${value};`).join("\n")}\n}\n`;
const styleDeclarations = (role, prefix = role) =>
  fields.map((field) => [
    field,
    `var(--nsh-${role}${field === "color" ? "" : "-" + field}, var(--_nsh-${prefix}-${field}))`,
  ]);

export function compileThemes(input) {
  const { themes, roles, families, baseCss } = input;
  const fallback = themes.find((theme) => theme.id === "default");
  let common = "/* Generated from validated theme JSON. Do not edit dist files. */\n";
  for (const mode of modes) {
    const styles = resolveStyles(fallback, mode, families);
    const selector =
      mode === "light"
        ? ":where(.nsh)"
        : ':where(.nsh[data-theme="dark"], [data-nsh-theme="dark"] .nsh:not([data-theme="light"]))';
    common += block(selector, [
      ["color-scheme", mode],
      ...Object.entries(styles).map(([key, value]) => [
        `--_nsh-${key}`,
        `var(--_nsh-${mode}-${key}, ${value})`,
      ]),
    ]);
  }
  common += baseCss;
  for (const role of roles)
    common += block(`:where(.nsh-token[data-token-type="${role}"])`, styleDeclarations(role));
  for (const [family, config] of families)
    for (const role of config.roles) {
      const selectors = config.documentKinds.flatMap((kind) => [
        `.nsh[data-language="${kind}"] .nsh-token[data-token-type="${role}"]:not([data-nsh-language])`,
        `.nsh-token[data-nsh-language="${kind}"][data-token-type="${role}"]`,
      ]);
      common += block(
        `:where(${selectors.join(",\n  ")})`,
        styleDeclarations(role, `${family}-${role}`),
      );
    }
  common += ':where(.nsh-token[data-modifiers~="deprecated"]) { text-decoration: line-through; }\n';
  const presets = new Map(
    themes.map((theme) => [
      theme.id,
      block(
        `:where([data-nsh-preset="${theme.id}"])`,
        modes.flatMap((mode) =>
          Object.entries(resolveStyles(theme, mode, families)).map(([key, value]) => [
            `--_nsh-${mode}-${key}`,
            value,
          ]),
        ),
      ),
    ]),
  );
  return { common, presets };
}

export function buildThemes(source = join(packageRoot, "src"), output = join(packageRoot, "dist")) {
  const input = loadThemes(source),
    compiled = compileThemes(input);
  rmSync(output, { recursive: true, force: true });
  mkdirSync(join(output, "languages"), { recursive: true });
  writeFileSync(join(output, "base.css"), compiled.common);
  for (const [id, css] of compiled.presets)
    writeFileSync(join(output, `${id}.css`), compiled.common + css);
  writeFileSync(
    join(output, "all.css"),
    compiled.common + [...compiled.presets.values()].join("\n"),
  );
  writeFileSync(
    join(output, "languages/typescript.css"),
    '/* Compatibility entry; family styles are included in default.css. */\n@import "../default.css";\n',
  );
  const catalog = input.themes.map(({ id, name, description }) => ({ id, name, description }));
  writeFileSync(
    join(output, "index.js"),
    `export const themes = Object.freeze(${JSON.stringify(catalog, null, 2)}.map(Object.freeze));\n`,
  );
  writeFileSync(
    join(output, "index.d.ts"),
    `export interface ThemePreset { readonly id: ${catalog.map(({ id }) => JSON.stringify(id)).join(" | ")}; readonly name: string; readonly description: string; }\nexport declare const themes: readonly ThemePreset[];\n`,
  );
  return input;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const result = buildThemes();
  console.log(
    `Built ${result.themes.length} themes with light/dark palettes and validated language overrides`,
  );
}
