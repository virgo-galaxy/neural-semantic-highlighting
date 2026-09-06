import eslint from "@eslint/js";
import { defineConfig, globalIgnores } from "eslint/config";
import simpleImportSort from "eslint-plugin-simple-import-sort";
import tseslint from "typescript-eslint";

export default defineConfig(
  globalIgnores([
    "dist/**",
    "node_modules/**",
    "packs/**/fixtures/**/source.*",
    "packs/**/fixtures/**/source",
  ]),
  {
    files: ["**/*.{js,ts}"],
    extends: [eslint.configs.recommended, tseslint.configs.recommended],
    plugins: {
      "simple-import-sort": simpleImportSort,
    },
    rules: {
      "simple-import-sort/imports": "error",
      "simple-import-sort/exports": "error",
    },
  },
);
