import { type BrowserModel, BrowserRuntime } from "@nsh/browser";
import { normalizeLanguageId, type SemanticPack } from "@nsh/core";

import { type ModelAsset, modelAssets } from "./model-assets.js";

export interface ModelAssetRequest {
  modelId: string;
  kind: "metadata" | "model";
  /** Content-addressed path relative to the deployed assets directory. */
  path: string;
  sha256: string;
}

export interface RemoteModelOptions {
  /** Public/static resource root, including the bucket/prefix when applicable. */
  modelBaseUrl?: string | URL;
  /** Resolve both metadata and model URLs, for example with private-object signatures. */
  resolveAssetUrl?: (asset: ModelAssetRequest) => string | URL | Promise<string | URL>;
}

type ExportMetadata = Pick<
  BrowserModel,
  | "id"
  | "manifest"
  | "contextBytes"
  | "schema"
  | "modifierThreshold"
  | "decoder"
  | "structuredDecoder"
  | "inferenceWindowing"
> & {
  format: string;
  model: { sha256: string; bytes: number };
};

function httpUrl(value: string | URL): URL {
  const url = new URL(value, typeof document === "undefined" ? undefined : document.baseURI);
  if (url.protocol !== "https:" && url.protocol !== "http:")
    throw new Error("Model resources require an HTTP or HTTPS URL");
  return url;
}

/** Only the small pinned catalog is bundled; decoder metadata and weights are lazy. */
export class RemoteModelSource {
  readonly #options: RemoteModelOptions;
  readonly #pending = new Map<string, Promise<BrowserModel>>();
  readonly #controller = new AbortController();

  constructor(options: RemoteModelOptions) {
    this.#options = options;
  }

  select(languages?: readonly string[]): readonly ModelAsset[] {
    const selected = new Map<string, ModelAsset>();
    const collect = (asset: ModelAsset) => {
      if (selected.has(asset.id)) return;
      selected.set(asset.id, asset);
      for (const id of asset.dependencies) {
        const dependency = modelAssets.find((item) => item.id === id);
        if (!dependency) throw new Error(`Missing remote model dependency: ${id}`);
        collect(dependency);
      }
    };
    if (languages === undefined) {
      for (const asset of modelAssets) collect(asset);
    } else {
      for (const language of languages) {
        const kind = normalizeLanguageId(language);
        const asset = modelAssets.find((item) =>
          item.manifest.documentKinds.some((entry) => entry.id === kind),
        );
        if (!asset) throw new Error(`Unsupported remote language: ${language}`);
        collect(asset);
      }
    }
    return [...selected.values()];
  }

  async #url(asset: ModelAsset, kind: ModelAssetRequest["kind"]): Promise<string> {
    if (this.#controller.signal.aborted) throw new Error("Browser highlighter is closed");
    const request: ModelAssetRequest = {
      modelId: asset.id,
      kind,
      path: kind === "model" ? asset.path : asset.metadata.path,
      sha256: kind === "model" ? asset.sha256 : asset.metadata.sha256,
    };
    let value: string | URL;
    if (this.#options.resolveAssetUrl) {
      value = await this.#options.resolveAssetUrl(request);
    } else {
      const base = httpUrl(this.#options.modelBaseUrl!);
      if (base.search || base.hash)
        throw new Error(
          "Use resolveAssetUrl for signed URLs; modelBaseUrl must have no query or fragment",
        );
      if (!base.pathname.endsWith("/")) base.pathname += "/";
      value = new URL(request.path, base);
    }
    if (this.#controller.signal.aborted) throw new Error("Browser highlighter is closed");
    if (typeof value !== "string" && !(value instanceof URL))
      throw new Error(`Invalid ${asset.id} ${kind} URL`);
    return httpUrl(value).href;
  }

  #load(asset: ModelAsset): Promise<BrowserModel> {
    const previous = this.#pending.get(asset.id);
    if (previous) return previous;
    const pending = (async () => {
      const url = await this.#url(asset, "metadata");
      const response = await fetch(url, { signal: this.#controller.signal });
      if (!response.ok) throw new Error(`Unable to load ${asset.id} metadata (${response.status})`);
      const raw = await response.arrayBuffer();
      const digest = Array.from(
        new Uint8Array(await crypto.subtle.digest("SHA-256", raw)),
        (byte) => byte.toString(16).padStart(2, "0"),
      ).join("");
      if (digest !== asset.metadata.sha256)
        throw new Error(`Browser model metadata integrity mismatch: ${asset.id}`);
      const metadata = JSON.parse(new TextDecoder().decode(raw)) as ExportMetadata;
      if (
        metadata.format !== "nsh-browser-model-v1" ||
        metadata.id !== asset.id ||
        metadata.model.sha256 !== asset.sha256 ||
        metadata.model.bytes !== asset.bytes
      )
        throw new Error(`Incompatible remote model metadata: ${asset.id}`);
      if (this.#controller.signal.aborted) throw new Error("Browser highlighter is closed");
      return {
        id: asset.id,
        manifest: asset.manifest,
        sha256: asset.sha256,
        contextBytes: metadata.contextBytes,
        schema: metadata.schema,
        modifierThreshold: metadata.modifierThreshold,
        decoder: metadata.decoder,
        structuredDecoder: metadata.structuredDecoder,
        inferenceWindowing: metadata.inferenceWindowing,
        modelUrl: () => this.#url(asset, "model"),
      };
    })().catch((error: unknown) => {
      this.#pending.delete(asset.id);
      throw error;
    });
    this.#pending.set(asset.id, pending);
    return pending;
  }

  createPack(asset: ModelAsset, runtime: BrowserRuntime): SemanticPack {
    return {
      manifest: asset.manifest,
      highlight: async (request) => {
        if (!request.source.length) return { offsetEncoding: "utf-16", spans: [] };
        const model = await this.#load(asset);
        return runtime.createPack(model).highlight(request);
      },
    };
  }

  close(): void {
    this.#controller.abort();
    this.#pending.clear();
  }
}
