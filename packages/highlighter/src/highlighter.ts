import { type BrowserModel, BrowserRuntime, type BrowserRuntimeOptions } from "@nsh/browser";
import {
  createHighlighter as createCoreHighlighter,
  type HighlightRequest,
  type HighlightResult,
  normalizeLanguageId,
  type SemanticPack,
} from "@nsh/core";
import { createCompositeHtmlPack } from "@nsh/core/composition/html";
import { createCompositeMarkdownPack } from "@nsh/core/composition/markdown";
import { createCompositePhpPack } from "@nsh/core/composition/php";
import { createCompositeSveltePack } from "@nsh/core/composition/svelte";
import { createCompositeVuePack } from "@nsh/core/composition/vue";
import { renderCodeToHtml, renderToHtml } from "@nsh/html";

import { type RemoteModelOptions, RemoteModelSource } from "./remote.js";
export type { ModelAssetRequest, RemoteModelOptions } from "./remote.js";
export type { BrowserRuntimeOptions, ModelCacheOptions } from "@nsh/browser";
export { clearModelCache, ModelAssetError } from "@nsh/browser";

export interface HighlighterOptions extends RemoteModelOptions, BrowserRuntimeOptions {
  /** Local descriptors, or content IDs/aliases when a remote source is configured. */
  languages?: readonly (BrowserModel | string)[];
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

/** Configure selected models explicitly; no Node/Python imports or source uploads. */
export function createHighlighter(options: HighlighterOptions = {}): BrowserHighlighter {
  const runtime = new BrowserRuntime(options);
  const base = new Map<string, SemanticPack>();
  const remote =
    options.modelBaseUrl !== undefined || options.resolveAssetUrl !== undefined
      ? new RemoteModelSource(options)
      : undefined;
  const models = new Map<string, BrowserModel>();
  function collect(model: BrowserModel) {
    const previous = models.get(model.id);
    if (previous && previous.sha256 !== model.sha256)
      throw new Error(`Conflicting model versions: ${model.id}`);
    if (previous) return;
    models.set(model.id, model);
    for (const dependency of model.dependencies ?? []) collect(dependency);
  }
  if (remote) {
    const languages = options.languages;
    if (languages?.some((language) => typeof language !== "string"))
      throw new Error(
        "Remote model selection accepts content IDs; use local descriptors without a remote source",
      );
    for (const asset of remote.select(languages as readonly string[] | undefined))
      base.set(asset.id, remote.createPack(asset, runtime));
  } else {
    for (const model of options.languages ?? []) {
      if (typeof model === "string")
        throw new Error("Set modelBaseUrl or resolveAssetUrl to select remote languages by name");
      collect(model);
    }
    for (const model of models.values()) base.set(model.id, runtime.createPack(model));
  }
  if (!base.size)
    throw new Error("Register at least one language model from @nsh/models/languages/<name>");
  const packs = [...base].map(([id, pack]) =>
    id === "markdown"
      ? createCompositeMarkdownPack({
          base: pack,
          resolveLanguage: (name) => {
            const kind = normalizeLanguageId(name);
            return kind !== "markdown" && core.supports(kind) ? kind : undefined;
          },
          highlightEmbedded: (request) => core.highlight(request),
        })
      : id === "php"
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
  let closed = false;
  const pending = new Set<(error: Error) => void>();
  const infer = (request: HighlightRequest): Promise<HighlightResult> => {
    if (closed) return Promise.reject(new Error("Browser highlighter is closed"));
    return new Promise((resolve, reject) => {
      pending.add(reject);
      core.highlight(request).then(
        (result) => {
          pending.delete(reject);
          resolve(result);
        },
        (error: unknown) => {
          pending.delete(reject);
          reject(error);
        },
      );
    });
  };
  const kindFor = normalizeLanguageId;
  const highlight = async (
    code: string,
    { language }: { language: string },
  ): Promise<HighlightedCode> => {
    const documentKind = kindFor(language);
    const result = await infer({ source: code, documentKind });
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
      infer({ source, documentKind: kindFor(documentKind) }),
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
    close: () => {
      closed = true;
      for (const reject of pending) reject(new Error("Browser highlighter is closed"));
      pending.clear();
      remote?.close();
      runtime.close();
    },
  };
}
