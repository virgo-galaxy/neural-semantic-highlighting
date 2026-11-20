import type { SemanticPack } from "@nsh/core";
import { describe, expect, it, vi } from "vitest";

import {
  defaultModelSource,
  type PlaygroundBrowserPack,
} from "../apps/playground/src/runtime/browser-pack.js";
import { PlaygroundRuntimeManager } from "../apps/playground/src/runtime/manager.js";

function pack(): PlaygroundBrowserPack {
  const base: SemanticPack = {
    manifest: { id: "test", documentKinds: [{ id: "typescript", extensions: [".ts"] }] },
    highlight: async () => ({ offsetEncoding: "utf-16", spans: [] }),
  };
  return { ...base, close: vi.fn() };
}
describe("Playground source switching", () => {
  it("reuses one initialization and closes the old pack when settings change", async () => {
    const first = pack(),
      second = pack();
    const create = vi.fn().mockResolvedValueOnce(first).mockResolvedValueOnce(second);
    const manager = new PlaygroundRuntimeManager(create);
    const a = manager.get(defaultModelSource),
      b = manager.get(defaultModelSource);
    expect(a).toBe(b);
    await a;
    expect(create).toHaveBeenCalledOnce();
    manager.reset();
    expect(first.close).toHaveBeenCalledOnce();
    await manager.get({
      ...defaultModelSource,
      mode: "remote",
      modelBaseUrl: "https://models.test/",
    });
    expect(create).toHaveBeenCalledTimes(2);
    manager.close();
    expect(second.close).toHaveBeenCalledOnce();
  });
  it("closes a late old initialization without replacing the newly selected source", async () => {
    let finish!: (value: PlaygroundBrowserPack) => void;
    const old = pack(),
      fresh = pack();
    const create = vi
      .fn()
      .mockImplementationOnce(
        () =>
          new Promise<PlaygroundBrowserPack>((resolve) => {
            finish = resolve;
          }),
      )
      .mockResolvedValueOnce(fresh);
    const manager = new PlaygroundRuntimeManager(create);
    const before = manager.get(defaultModelSource);
    const rejected = expect(before).rejects.toThrow("source changed");
    manager.reset();
    const current = await manager.get({
      ...defaultModelSource,
      mode: "remote",
      modelBaseUrl: "https://models.test/",
    });
    finish(old);
    await rejected;
    expect(old.close).toHaveBeenCalledOnce();
    expect(await manager.get(defaultModelSource)).toBe(current);
    expect(fresh.close).not.toHaveBeenCalled();
    manager.close();
  });
  it("allows initialization failure to be retried and blocks work after disposal", async () => {
    const fresh = pack();
    const create = vi.fn().mockRejectedValueOnce(new Error("failed")).mockResolvedValueOnce(fresh);
    const manager = new PlaygroundRuntimeManager(create);
    await expect(manager.get(defaultModelSource)).rejects.toThrow("failed");
    await manager.get(defaultModelSource);
    manager.close();
    await expect(manager.get(defaultModelSource)).rejects.toThrow("closed");
    expect(create).toHaveBeenCalledTimes(2);
  });
});
