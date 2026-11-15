import {
  createHighlighter as createConfiguredHighlighter,
  type HighlighterOptions,
} from "./highlighter.js";
import assembly from "./languages/assembly.js";
import awk from "./languages/awk.js";
import bash from "./languages/bash.js";
import bat from "./languages/bat.js";
import c from "./languages/c.js";
import cpp from "./languages/cpp.js";
import csharp from "./languages/csharp.js";
import css from "./languages/css.js";
import dart from "./languages/dart.js";
import go from "./languages/go.js";
import html from "./languages/html.js";
import ini from "./languages/ini.js";
import java from "./languages/java.js";
import json from "./languages/json.js";
import kotlin from "./languages/kotlin.js";
import lua from "./languages/lua.js";
import perl from "./languages/perl.js";
import php from "./languages/php.js";
import powershell from "./languages/powershell.js";
import python from "./languages/python.js";
import r from "./languages/r.js";
import ruby from "./languages/ruby.js";
import rust from "./languages/rust.js";
import scala from "./languages/scala.js";
import sql from "./languages/sql.js";
import svelte from "./languages/svelte.js";
import swift from "./languages/swift.js";
import toml from "./languages/toml.js";
import typescript from "./languages/typescript.js";
import vue from "./languages/vue.js";
import yaml from "./languages/yaml.js";
import zig from "./languages/zig.js";

export type { BrowserHighlighter, HighlightedCode, HighlighterOptions } from "./highlighter.js";
export function createHighlighter(options: HighlighterOptions = {}) {
  return createConfiguredHighlighter({
    ...options,
    languages: options.languages ?? [
      typescript,
      go,
      css,
      html,
      vue,
      python,
      bash,
      perl,
      awk,
      sql,
      powershell,
      bat,
      assembly,
      java,
      csharp,
      c,
      cpp,
      php,
      svelte,
      rust,
      zig,
      dart,
      swift,
      kotlin,
      r,
      scala,
      ruby,
      lua,
      json,
      yaml,
      toml,
      ini,
    ],
  });
}
