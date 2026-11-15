import { type BrowserModel, BrowserRuntime } from "@nsh/browser";
import {
  createHighlighter as createCoreHighlighter,
  type HighlightRequest,
  type HighlightResult,
  type SemanticPack,
} from "@nsh/core";
import { createCompositeHtmlPack } from "@nsh/core/composition/html";
import { createCompositePhpPack } from "@nsh/core/composition/php";
import { createCompositeSveltePack } from "@nsh/core/composition/svelte";
import { createCompositeVuePack } from "@nsh/core/composition/vue";
import { renderCodeToHtml, renderToHtml } from "@nsh/html";

export interface HighlighterOptions {
  languages?: readonly BrowserModel[];
}

export interface HighlightedCode {
  language: string;
  /** Escaped token markup for an existing <pre class="nsh"><code>. */
  value: string;
  /** Complete <pre class="nsh"><code> markup, ready for insertion. */
  html: string;
  result: HighlightResult;
}

export interface BrowserHighlighter {
  highlight(code: string, options: { language: string }): Promise<HighlightedCode>;
  highlightTokens(request: HighlightRequest): Promise<HighlightResult>;
  highlightElement(element: HTMLElement, options?: { language?: string }): Promise<HighlightedCode>;
  supports(language: string): boolean;
  languages(): readonly string[];
  close(): void;
}

const aliases: Readonly<Record<string, string>> = {
  js: "javascript",
  yml: "yaml",
  env: "dotenv",
  ".env": "dotenv",
  cfg: "ini",
  editorconfig: "ini",
  ts: "typescript",
  sh: "bash",
  shell: "bash",
  zsh: "bash",
  csh: "bash",
  tcsh: "bash",
  pwsh: "powershell",
  ps1: "powershell",
  cmd: "bat",
  asm: "assembly",
  nasm: "assembly",
  masm: "assembly",
  gas: "assembly",
  py: "python",
  rs: "rust",
  rb: "ruby",
  rake: "ruby",
  gemspec: "ruby",
  gemfile: "ruby",
  rakefile: "ruby",
  flutter: "dart",
  kt: "kotlin",
  kts: "kotlin",
  "kotlin-script": "kotlin",
  cs: "csharp",
  "c#": "csharp",
  "c++": "cpp",
  cxx: "cpp",
};

/** Configure selected models explicitly; no Node/Python imports or source uploads. */
export function createHighlighter(options: HighlighterOptions): BrowserHighlighter {
  const models = new Map<string, BrowserModel>();
  function collect(model: BrowserModel) {
    const previous = models.get(model.id);
    if (previous && previous.sha256 !== model.sha256)
      throw new Error(`Conflicting model versions: ${model.id}`);
    if (previous) return;
    models.set(model.id, model);
    for (const dependency of model.dependencies ?? []) collect(dependency);
  }
  for (const model of options.languages ?? []) collect(model);
  if (!models.size) throw new Error("Register at least one language model");
  const runtime = new BrowserRuntime();
  const base = new Map<string, SemanticPack>();
  for (const model of models.values()) base.set(model.id, runtime.createPack(model));
  const packs = [...base].map(([id, pack]) =>
    id === "php"
      ? createCompositePhpPack({
          base: pack,
          highlightEmbedded: (request) => core.highlight(request),
        })
      : id === "html"
        ? createCompositeHtmlPack({
            base: pack,
            highlightEmbedded: (request) => core.highlight(request),
          })
        : id === "vue"
          ? createCompositeVuePack({
              base: pack,
              highlightEmbedded: (request) => core.highlight(request),
            })
          : id === "svelte"
            ? createCompositeSveltePack({
                base: pack,
                highlightEmbedded: (request) => core.highlight(request),
              })
            : pack,
  );
  const core = createCoreHighlighter({ packs });
  const kindFor = (language: string) => aliases[language.toLowerCase()] ?? language.toLowerCase();
  const highlight = async (
    code: string,
    { language }: { language: string },
  ): Promise<HighlightedCode> => {
    const documentKind = kindFor(language);
    const result = await core.highlight({ source: code, documentKind });
    const request = { source: code, documentKind, result };
    return {
      language: documentKind,
      result,
      value: renderCodeToHtml(request),
      html: renderToHtml(request),
    };
  };
  return {
    highlight,
    highlightTokens: ({ source, documentKind }) =>
      core.highlight({ source, documentKind: kindFor(documentKind) }),
    async highlightElement(element, options = {}) {
      const language =
        options.language ??
        element.dataset.language ??
        [...element.classList].find((name) => name.startsWith("language-"))?.slice(9) ??
        element.parentElement?.dataset.language;
      if (!language)
        throw new Error("Set a language, for example language-tsx or data-language=tsx");
      const result = await highlight(element.textContent ?? "", { language });
      element.innerHTML = result.value;
      const wrapper = element.parentElement?.tagName === "PRE" ? element.parentElement : element;
      wrapper.classList.add("nsh");
      wrapper.dataset.language = result.language;
      return result;
    },
    supports: (language) => core.supports(kindFor(language)),
    languages: () => core.documentKinds(),
    close: () => runtime.close(),
  };
}
