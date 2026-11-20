import { readFileSync, writeFileSync } from "node:fs";

import { contentCategories, contentTypes } from "@nsh/core/catalog";
import { format, resolveConfig } from "prettier";

// Build packages first. Only these bounded sections are generated; evaluation
// reports and their historical measurements remain authored evidence.
for (const category of contentCategories) {
  const filename = `docs/${category.id === "code" ? "code-languages" : "file-formats"}.md`;
  const rows = contentTypes
    .filter((entry) => entry.category === category.id)
    .map((entry) => {
      const model = [
        `\`${entry.modelId}\``,
        ...(entry.modelDependencies ?? []).map((id) => `+ \`${id}\``),
      ].join(" ");
      return `| ${entry.label} | \`${entry.id}\` | ${entry.aliases.map((alias) => `\`${alias}\``).join(", ") || "—"} | ${model} |`;
    });
  const table = [
    "<!-- catalog:start -->",
    "",
    "| Name | Content ID | Accepted aliases | Model / direct dependencies |",
    "| --- | --- | --- | --- |",
    ...rows,
    "",
    "<!-- catalog:end -->",
  ].join("\n");
  const source = readFileSync(filename, "utf8");
  writeFileSync(
    filename,
    await format(source.replace(/<!-- catalog:start -->[\s\S]*?<!-- catalog:end -->/u, table), {
      ...(await resolveConfig(filename)),
      filepath: filename,
    }),
  );
}
