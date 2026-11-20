export interface ModelCacheOptions {
  persistent?: boolean;
  /** Best-effort shared CacheStorage budget, in bytes. */
  maxBytes?: number;
}
export interface BrowserRuntimeOptions {
  cache?: ModelCacheOptions;
  maxLoadedModels?: number;
  downloadTimeoutMs?: number;
}
export interface RuntimePolicy {
  cache: { persistent: boolean; maxBytes: number };
  maxLoadedModels: number;
  downloadTimeoutMs: number;
}
export function runtimePolicy(options: BrowserRuntimeOptions = {}): RuntimePolicy {
  const result = {
    cache: {
      persistent: options.cache?.persistent ?? true,
      maxBytes: options.cache?.maxBytes ?? 64_000_000,
    },
    maxLoadedModels: options.maxLoadedModels ?? 4,
    downloadTimeoutMs: options.downloadTimeoutMs ?? 30_000,
  };
  if (
    typeof result.cache.persistent !== "boolean" ||
    !Number.isSafeInteger(result.cache.maxBytes) ||
    result.cache.maxBytes < 0 ||
    !Number.isInteger(result.maxLoadedModels) ||
    result.maxLoadedModels < 1 ||
    !Number.isInteger(result.downloadTimeoutMs) ||
    result.downloadTimeoutMs < 1 ||
    result.downloadTimeoutMs > 2_147_483_647
  )
    throw new Error("Invalid browser model cache or download policy");
  return result;
}

type ErrorCode = "http" | "network" | "timeout" | "integrity";
export interface ModelAssetFailure {
  name: "ModelAssetError";
  code: ErrorCode;
  modelId: string;
  kind: "model" | "metadata";
  message: string;
  status?: number;
}
export class ModelAssetError extends Error {
  readonly name = "ModelAssetError";
  constructor(
    readonly code: ErrorCode,
    readonly modelId: string,
    readonly kind: "model" | "metadata",
    readonly status?: number,
  ) {
    super(
      code === "http"
        ? `Unable to load ${modelId} ${kind} (${status})`
        : code === "timeout"
          ? `Loading ${modelId} ${kind} timed out; retry or check the resource host`
          : code === "integrity"
            ? `Browser model${kind === "metadata" ? " metadata" : ""} integrity mismatch: ${modelId}`
            : `Unable to load ${modelId} ${kind}; check network access and CORS`,
    );
  }
  toJSON(): ModelAssetFailure {
    return {
      name: this.name,
      code: this.code,
      modelId: this.modelId,
      kind: this.kind,
      message: this.message,
      status: this.status,
    };
  }
}

const CACHE_NAME = "nsh-model-assets-v1";
const keyFor = (sha256: string) => `https://nsh-model-cache.invalid/v1/${sha256}`;
const hash = async (bytes: ArrayBuffer) =>
  Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");

export async function clearModelCache(): Promise<boolean> {
  try {
    return typeof caches !== "undefined" && (await caches.delete(CACHE_NAME));
  } catch {
    return false;
  }
}

interface AssetRequest {
  modelId: string;
  kind: "model" | "metadata";
  sha256: string;
  url(): string | Promise<string>;
  signal?: AbortSignal;
}

/** Cache keys contain only digests; neither source text nor signed URLs are persisted. */
export class ModelAssetCache {
  readonly #policy: RuntimePolicy;
  #disabled = false;
  constructor(options: BrowserRuntimeOptions = {}) {
    this.#policy = runtimePolicy(options);
  }

  async #open(): Promise<Cache | undefined> {
    if (!this.#policy.cache.persistent || !this.#policy.cache.maxBytes || this.#disabled) return;
    try {
      return typeof caches === "undefined" ? undefined : await caches.open(CACHE_NAME);
    } catch {
      this.#disabled = true;
      return;
    }
  }

  async #write(cache: Cache, key: string, bytes: ArrayBuffer): Promise<void> {
    if (bytes.byteLength > this.#policy.cache.maxBytes) return;
    try {
      await cache.put(
        key,
        new Response(bytes.slice(0), {
          headers: {
            "X-NSH-Bytes": String(bytes.byteLength),
            "X-NSH-Accessed": String(Date.now()),
          },
        }),
      );
      const entries = await Promise.all(
        (await cache.keys()).map(async (request) => {
          const response = await cache.match(request);
          return {
            request,
            bytes: Number(response?.headers.get("X-NSH-Bytes") ?? 0),
            accessed: Number(response?.headers.get("X-NSH-Accessed") ?? 0),
          };
        }),
      );
      let total = entries.reduce((sum, entry) => sum + entry.bytes, 0);
      for (const entry of entries.sort((a, b) => a.accessed - b.accessed)) {
        if (total <= this.#policy.cache.maxBytes) break;
        await cache.delete(entry.request);
        total -= entry.bytes;
      }
    } catch {
      this.#disabled = true;
    }
  }

  async load(request: AssetRequest): Promise<ArrayBuffer> {
    const controller = new AbortController();
    const cancel = () => controller.abort(request.signal?.reason);
    if (request.signal?.aborted) cancel();
    else request.signal?.addEventListener("abort", cancel, { once: true });
    const timer = setTimeout(
      () => controller.abort(new ModelAssetError("timeout", request.modelId, request.kind)),
      this.#policy.downloadTimeoutMs,
    );
    let onAbort!: () => void;
    const interrupted = new Promise<never>((_, reject) => {
      onAbort = () => reject(controller.signal.reason);
      if (controller.signal.aborted) onAbort();
      else controller.signal.addEventListener("abort", onAbort, { once: true });
    });
    const operation = (async () => {
      const cache = await this.#open();
      const key = keyFor(request.sha256);
      if (cache) {
        try {
          const cached = await cache.match(key);
          if (cached) {
            const bytes = await cached.arrayBuffer();
            if ((await hash(bytes)) === request.sha256) {
              controller.signal.throwIfAborted();
              await this.#write(cache, key, bytes);
              return bytes;
            }
            await cache.delete(key);
          }
        } catch (error) {
          controller.signal.throwIfAborted();
          void error;
          this.#disabled = true;
        }
      }
      controller.signal.throwIfAborted();
      const url = await request.url();
      controller.signal.throwIfAborted();
      let response: Response;
      let bytes: ArrayBuffer;
      try {
        response = await fetch(url, { signal: controller.signal });
        if (!response.ok)
          throw new ModelAssetError("http", request.modelId, request.kind, response.status);
        bytes = await response.arrayBuffer();
      } catch (error) {
        controller.signal.throwIfAborted();
        if (error instanceof ModelAssetError) throw error;
        throw new ModelAssetError("network", request.modelId, request.kind);
      }
      if ((await hash(bytes)) !== request.sha256)
        throw new ModelAssetError("integrity", request.modelId, request.kind);
      controller.signal.throwIfAborted();
      if (cache && !this.#disabled) await this.#write(cache, key, bytes);
      return bytes;
    })();
    try {
      return await Promise.race([operation, interrupted]);
    } finally {
      clearTimeout(timer);
      request.signal?.removeEventListener("abort", cancel);
      controller.signal.removeEventListener("abort", onAbort);
    }
  }
}
