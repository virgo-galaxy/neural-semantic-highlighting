import { cpSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

import { describe, expect, it } from "vitest";

import {
  compileThemes,
  loadThemes,
  mergeStyle,
  resolveStyles,
} from "../packages/themes/web/scripts/build.mjs";

const source = resolve("packages/themes/web/src");
const input = loadThemes(source);

function luminance(color) {
  const parts = color
    .slice(1)
    .match(/../g)
    .map((value) => parseInt(value, 16) / 255)
    .map((value) => (value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4));
  return parts[0] * 0.2126 + parts[1] * 0.7152 + parts[2] * 0.0722;
}
function contrast(a, b) {
  const x = luminance(a),
    y = luminance(b);
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
}

describe("theme configuration", () => {
  it("loads neutral preset names, complete paired palettes and all TS/CSS document kinds", () => {
    expect(input.themes.map(({ id }) => id)).toEqual(["default", "muted", "contrast"]);
    expect(input.families.get("typescript").documentKinds).toContain("typescript-esm-declaration");
    expect(input.families.get("css").documentKinds).toEqual(["css", "scss", "less"]);
    // constructor is a real role, not an inherited Object property in sparse overrides.
    expect(input.roles).toContain("constructor");
  });
  it("merges individual style properties and allows false to clear an inherited style", () => {
    expect(mergeStyle({ color: "#000000", italic: true }, { color: "#111111" })).toEqual({
      color: "#111111",
      italic: true,
    });
    expect(mergeStyle({ color: "#000000", italic: true }, { italic: false })).toEqual({
      color: "#000000",
      italic: false,
    });
  });
  it("falls back to the selected preset instead of retaining another preset's language colors", () => {
    const muted = input.themes.find(({ id }) => id === "muted");
    const styles = resolveStyles(muted, "light", input.families);
    expect(styles["typescript-class-color"]).toBe(styles["class-color"]);
    expect(styles["css-class-color"]).not.toBe(styles["class-color"]);
    expect(styles["typescript-class-color"]).not.toBe(
      resolveStyles(input.themes[0], "light", input.families)["typescript-class-color"],
    );
  });
  it("keeps every supplied semantic color and selection foreground at readable contrast", () => {
    for (const theme of input.themes)
      for (const mode of ["light", "dark"]) {
        const styles = resolveStyles(theme, mode, input.families);
        for (const [key, color] of Object.entries(styles).filter(([key]) => key.endsWith("-color")))
          expect(
            contrast(color, styles.background),
            `${theme.id}/${mode}/${key}`,
          ).toBeGreaterThanOrEqual(4.5);
        expect(
          contrast(styles["selection-foreground"], styles["selection-background"]),
        ).toBeGreaterThanOrEqual(4.5);
      }
  });
  it.each([
    [
      "invalid color",
      "default/light.json",
      (data) => {
        data.tokens.string = "url(unsafe)";
      },
    ],
    [
      "unknown role",
      "default/light.json",
      (data) => {
        data.tokens.strnig = "#000000";
      },
    ],
    [
      "incomplete palette",
      "default/dark.json",
      (data) => {
        delete data.tokens.keyword;
      },
    ],
    [
      "bad style type",
      "default/languages/css.json",
      (data) => {
        data.light.tokens.class = { italic: "yes" };
      },
    ],
    [
      "conflicting language kinds",
      "default/languages/css.json",
      (data) => {
        data.documentKinds = ["typescript"];
      },
    ],
  ])("rejects %s at build time", (_, file, modify) => {
    const folder = mkdtempSync(join(tmpdir(), "nsh-theme-"));
    try {
      cpSync(source, folder, { recursive: true });
      const path = join(folder, "themes", file),
        data = JSON.parse(readFileSync(path, "utf8"));
      modify(data);
      writeFileSync(path, JSON.stringify(data));
      expect(() => loadThemes(folder)).toThrow();
    } finally {
      rmSync(folder, { recursive: true, force: true });
    }
  });
});

describe("theme distribution", () => {
  it("ships the same self-contained CSS through the public highlighter entry points", () => {
    const compiled = compileThemes(input);
    for (const [id, css] of compiled.presets) {
      expect(readFileSync(`packages/highlighter/dist/themes/${id}.css`, "utf8")).toBe(
        compiled.common + css,
      );
    }
    expect(readFileSync("packages/highlighter/dist/theme.css", "utf8")).toBe(
      readFileSync("packages/highlighter/dist/themes/default.css", "utf8"),
    );
    expect(compiled.common).toContain('data-nsh-language="css"');
    expect(compiled.common).toContain(":not([data-nsh-language])");
    expect(compiled.common).toContain("var(--nsh-class,");
  });
});
