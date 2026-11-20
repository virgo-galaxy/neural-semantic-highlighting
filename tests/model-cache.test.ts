import { createHash } from "node:crypto";

import { BrowserRuntime, ModelAssetError as PublicAssetError } from "@nsh/browser";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  clearModelCache,
  ModelAssetCache,
  ModelAssetError,
  runtimePolicy,
} from "../packages/runtimes/browser/src/assets.js";
import { SessionPool } from "../packages/runtimes/browser/src/sessions.js";

class MemoryCache {
  readonly entries = new Map<string, Response>();
  async match(key: string | Request) {
    return this.entries.get(typeof key === "string" ? key : key.url)?.clone();
  }
  async put(key: string, response: Response) {
    this.entries.set(key, response.clone());
  }
  async delete(key: string | Request) {
    return this.entries.delete(typeof key === "string" ? key : key.url);
  }
  async keys() {
    return [...this.entries.keys()].map((url) => new Request(url));
  }
}
const digest = (text: string) => createHash("sha256").update(text).digest("hex");
const request = (text: string) => ({
  modelId: "test",
  kind: "model" as const,
  sha256: digest(text),
  url: vi.fn(() => "https://private.test/model.onnx?secret=temporary"),
});
function setup(text: string) {
  const cache = new MemoryCache();
  vi.stubGlobal("caches", {
    open: vi.fn(async () => cache),
    delete: vi.fn(async () => {
      cache.entries.clear();
      return true;
    }),
  });
  const fetcher = vi.fn(async () => new Response(text));
  vi.stubGlobal("fetch", fetcher);
  return { cache, fetcher };
}
afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("versioned browser asset cache", () => {
  it("reuses verified bytes across loader instances without persisting signed URLs", async () => {
    const { cache, fetcher } = setup("abc");
    const asset = request("abc");
    await new ModelAssetCache().load(asset);
    const second = new ModelAssetCache();
    await second.load(asset);
    expect(fetcher).toHaveBeenCalledOnce();
    expect(asset.url).toHaveBeenCalledOnce();
    expect([...cache.entries.keys()]).toEqual([
      `https://nsh-model-cache.invalid/v1/${asset.sha256}`,
    ]);
    expect(JSON.stringify([...cache.entries.keys()])).not.toContain("secret");
    expect(await clearModelCache()).toBe(true);
    expect(cache.entries.size).toBe(0);
  });
  it("uses a different cache key for a new revision and evicts old least-recently-used bytes", async () => {
    const { cache, fetcher } = setup("aaa");
    let clock = 1;
    vi.spyOn(Date, "now").mockImplementation(() => clock++);
    const loader = new ModelAssetCache({ cache: { maxBytes: 6 } });
    await loader.load(request("aaa"));
    fetcher.mockResolvedValueOnce(new Response("bbb"));
    await loader.load(request("bbb"));
    await loader.load(request("aaa"));
    fetcher.mockResolvedValueOnce(new Response("ccc"));
    await loader.load(request("ccc"));
    expect(cache.entries.has(`https://nsh-model-cache.invalid/v1/${digest("aaa")}`)).toBe(true);
    expect(cache.entries.has(`https://nsh-model-cache.invalid/v1/${digest("bbb")}`)).toBe(false);
    expect(cache.entries.size).toBe(2);
  });
  it("repairs a corrupted cached asset with one verified network download", async () => {
    const { cache, fetcher } = setup("good");
    const asset = request("good");
    await cache.put(`https://nsh-model-cache.invalid/v1/${asset.sha256}`, new Response("bad"));
    const result = await new ModelAssetCache().load(asset);
    expect(new TextDecoder().decode(result)).toBe("good");
    expect(fetcher).toHaveBeenCalledOnce();
  });
  it("does not store bad network bytes, and surfaces a typed integrity error", async () => {
    const { cache } = setup("wrong");
    await expect(new ModelAssetCache().load(request("good"))).rejects.toMatchObject({
      name: "ModelAssetError",
      code: "integrity",
    });
    expect(cache.entries.size).toBe(0);
  });
  it("falls back when CacheStorage is unavailable or its quota is exhausted", async () => {
    const { cache, fetcher } = setup("abc");
    vi.spyOn(cache, "put").mockRejectedValue(new DOMException("Full", "QuotaExceededError"));
    await expect(new ModelAssetCache().load(request("abc"))).resolves.toBeInstanceOf(ArrayBuffer);
    vi.stubGlobal("caches", {
      open: vi.fn(async () => {
        throw new Error("unavailable");
      }),
    });
    await expect(new ModelAssetCache().load(request("abc"))).resolves.toBeInstanceOf(ArrayBuffer);
    expect(fetcher).toHaveBeenCalledTimes(2);
  });
  it("can disable persistence and skips files larger than its budget", async () => {
    const { cache } = setup("abc");
    await new ModelAssetCache({ cache: { persistent: false } }).load(request("abc"));
    await new ModelAssetCache({ cache: { maxBytes: 2 } }).load(request("abc"));
    expect(cache.entries.size).toBe(0);
  });
  it("times out unresolved download URLs and never fetches after they resolve late", async () => {
    setup("abc");
    vi.useFakeTimers();
    let finish!: (url: string) => void;
    const asset = {
      ...request("abc"),
      url: () =>
        new Promise<string>((resolve) => {
          finish = resolve;
        }),
    };
    const result = new ModelAssetCache({ downloadTimeoutMs: 10 }).load(asset);
    const rejected = expect(result).rejects.toMatchObject({ code: "timeout" });
    await vi.advanceTimersByTimeAsync(11);
    await rejected;
    finish("https://private.test/late.onnx");
    await Promise.resolve();
    await Promise.resolve();
    expect(fetch).not.toHaveBeenCalled();
  });
  it("surfaces HTTP and network failures without caching them", async () => {
    const { cache, fetcher } = setup("abc");
    fetcher.mockResolvedValueOnce(new Response("", { status: 403 }));
    await expect(new ModelAssetCache().load(request("abc"))).rejects.toMatchObject({
      code: "http",
      status: 403,
    });
    fetcher.mockRejectedValueOnce(new TypeError("Failed to fetch"));
    await expect(new ModelAssetCache().load(request("abc"))).rejects.toMatchObject({
      code: "network",
    });
    expect(cache.entries.size).toBe(0);
    expect(new ModelAssetError("http", "test", "model", 403).toJSON()).toMatchObject({
      code: "http",
      status: 403,
    });
  });
  it("validates cache limits before starting any browser work", () => {
    expect(runtimePolicy().maxLoadedModels).toBe(4);
    for (const options of [
      { maxLoadedModels: 0 },
      { downloadTimeoutMs: 0 },
      { cache: { maxBytes: -1 } },
    ])
      expect(() => runtimePolicy(options)).toThrow("policy");
  });
});

describe("bounded inference sessions", () => {
  it("preserves actionable asset errors across the Worker boundary", async () => {
    const workers: EventTarget[] = [];
    let id = 0;
    class FailureWorker extends EventTarget {
      constructor() {
        super();
        workers.push(this);
      }
      postMessage(message: { id: number }) {
        id = message.id;
      }
      terminate() {}
    }
    vi.stubGlobal("Worker", FailureWorker);
    const runtime = new BrowserRuntime();
    const pack = runtime.createPack({
      id: "test",
      manifest: { id: "test", documentKinds: [{ id: "test", extensions: [] }] },
      modelUrl: () => "https://models.test/model.onnx",
      sha256: "test",
      contextBytes: 512,
      schema: { tokenTypes: ["keyword"], modifiers: [] },
      modifierThreshold: 0.6,
    });
    const result = pack.highlight({ source: "x", documentKind: "test" });
    const rejected = expect(result).rejects.toBeInstanceOf(PublicAssetError);
    workers[0].dispatchEvent(
      new MessageEvent("message", {
        data: { id, error: new PublicAssetError("http", "test", "model", 403).toJSON() },
      }),
    );
    await rejected;
    await expect(result).rejects.toMatchObject({ code: "http", status: 403, modelId: "test" });
    runtime.close();
  });
  it("reuses sessions and releases the least-recently-used idle session", async () => {
    const pool = new SessionPool<{ release: () => Promise<void> }>();
    const a = { release: vi.fn(async () => {}) },
      b = { release: vi.fn(async () => {}) },
      c = { release: vi.fn(async () => {}) };
    const make = vi.fn(async () => a);
    await pool.use("a", 2, make, async () => 1);
    await pool.use(
      "b",
      2,
      async () => b,
      async () => 1,
    );
    await pool.use("a", 2, make, async () => 1);
    await pool.use(
      "c",
      2,
      async () => c,
      async () => 1,
    );
    expect(make).toHaveBeenCalledOnce();
    expect(b.release).toHaveBeenCalledOnce();
    expect(a.release).not.toHaveBeenCalled();
  });
  it("never releases active work and discards a failed session for retry", async () => {
    const pool = new SessionPool<{ release: () => Promise<void> }>();
    const a = { release: vi.fn(async () => {}) },
      b = { release: vi.fn(async () => {}) };
    let finish!: () => void;
    const pending = pool.use(
      "a",
      1,
      async () => a,
      () =>
        new Promise<void>((resolve) => {
          finish = resolve;
        }),
    );
    await vi.waitFor(() => expect(finish).toBeTypeOf("function"));
    await pool.use(
      "b",
      1,
      async () => b,
      async () => 1,
    );
    expect(a.release).not.toHaveBeenCalled();
    finish();
    await pending;
    await expect(
      pool.use(
        "a",
        1,
        async () => a,
        async () => {
          throw new Error("run failed");
        },
      ),
    ).rejects.toThrow("run failed");
    expect(a.release).toHaveBeenCalledOnce();
    const create = vi.fn(async () => b);
    await pool.use("a", 1, create, async () => 1);
    expect(create).toHaveBeenCalledOnce();
  });
});
