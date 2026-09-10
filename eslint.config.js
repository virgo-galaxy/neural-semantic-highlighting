import eslint from "@eslint/js";
import { defineConfig, globalIgnores } from "eslint/config";
import simpleImportSort from "eslint-plugin-simple-import-sort";
import vue from "eslint-plugin-vue";
import tseslint from "typescript-eslint";
import vueParser from "vue-eslint-parser";

export default defineConfig(
  globalIgnores([
    ".venv/**",
    "artifacts/**",
    "**/dist/**",
    "**/node_modules/**",
    "packs/**/fixtures/**/source.*",
    "packs/**/fixtures/**/source",
    "apps/playground/src/views/highlighter/examples/*/*",
  ]),
  {
    files: ["**/*.{js,ts}"],
    extends: [eslint.configs.recommended, tseslint.configs.recommended],
    plugins: {
      "simple-import-sort": simpleImportSort,
    },
    rules: {
      "no-undef": "off",
      "simple-import-sort/imports": "error",
      "simple-import-sort/exports": "error",
    },
  },
  {
    files: ["apps/playground/**/*.vue"],
    extends: [
      eslint.configs.recommended,
      tseslint.configs.recommended,
      vue.configs["flat/essential"],
    ],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tseslint.parser,
        extraFileExtensions: [".vue"],
      },
    },
    plugins: {
      "simple-import-sort": simpleImportSort,
    },
    rules: {
      "no-undef": "off",
      "simple-import-sort/imports": "error",
      "simple-import-sort/exports": "error",
    },
  },
  {
    files: ["apps/playground/src/**/*.{js,ts,vue}"],
    languageOptions: {
      globals: {
        document: "readonly",
        window: "readonly",
        navigator: "readonly",
        location: "readonly",
        fetch: "readonly",
      },
    },
  },
);
