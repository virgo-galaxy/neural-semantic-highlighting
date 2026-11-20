import { codeTypes } from "./code.js";
import { fileFormats } from "./formats.js";
import type { ContentType } from "./types.js";

export type { ContentCategory, ContentType } from "./types.js";

export const contentCategories = Object.freeze([
  Object.freeze({ id: "code" as const, label: "Code languages" }),
  Object.freeze({ id: "formats" as const, label: "File formats" }),
]);

export const contentTypes: readonly ContentType[] = Object.freeze(
  [...codeTypes, ...fileFormats].map((entry) =>
    Object.freeze({
      ...entry,
      aliases: Object.freeze([...entry.aliases]),
      extensions: Object.freeze([...entry.extensions]),
      frameworks: entry.frameworks && Object.freeze([...entry.frameworks]),
      modelDependencies: entry.modelDependencies && Object.freeze([...entry.modelDependencies]),
      fileVariants:
        entry.fileVariants &&
        Object.freeze(
          entry.fileVariants.map((variant) =>
            Object.freeze({ ...variant, extensions: Object.freeze([...variant.extensions]) }),
          ),
        ),
    }),
  ),
);

const names = new Map<string, { kind: string; entry: ContentType }>();
for (const entry of contentTypes) {
  const register = (name: string, kind: string) => {
    const key = name.toLowerCase();
    if (names.has(key)) throw new Error(`Duplicate content name: ${name}`);
    names.set(key, { kind, entry });
  };
  const kind = entry.documentKind ?? entry.id;
  register(entry.id, kind);
  for (const alias of entry.aliases) register(alias, kind);
  for (const variant of entry.fileVariants ?? []) register(variant.id, variant.id);
}

/** Resolve only explicitly registered names; unknown names remain unsupported. */
export function normalizeLanguageId(language: string): string {
  const id = language.toLowerCase();
  return names.get(id)?.kind ?? id;
}

export function getContentType(name: string): ContentType | undefined {
  return names.get(name.toLowerCase())?.entry;
}

const filenames = contentTypes
  .flatMap((entry) => {
    const variants = entry.fileVariants ?? [];
    const variantExtensions = new Set(variants.flatMap((variant) => [...variant.extensions]));
    return [
      ...entry.extensions
        .filter((extension) => !variantExtensions.has(extension))
        .map((extension) => ({ extension, kind: entry.documentKind ?? entry.id, entry })),
      ...variants.flatMap((variant) =>
        variant.extensions.map((extension) => ({ extension, kind: variant.id, entry })),
      ),
    ];
  })
  .sort((a, b) => b.extension.length - a.extension.length);

/** Explicit filename helper, not content/language auto-detection by the highlighter. */
export function documentKindForFilename(
  filename: string,
  contentTypeId?: string,
): string | undefined {
  const entry = contentTypeId ? getContentType(contentTypeId) : undefined;
  if (contentTypeId && !entry) return undefined;
  // JSONC can use .json; dotenv examples can use .env.local or extensionless names.
  if (entry?.id === "jsonc" || entry?.id === "dotenv") return entry.id;
  const match = filenames.find(
    (item) =>
      (!entry || item.entry.modelId === entry.modelId) &&
      (item.extension.startsWith(".")
        ? filename.endsWith(item.extension)
        : filename === item.extension),
  );
  return match?.kind ?? (contentTypeId ? normalizeLanguageId(contentTypeId) : undefined);
}
