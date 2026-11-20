interface Releasable {
  release(): Promise<void>;
}
interface Entry<T> {
  pending: Promise<T>;
  active: number;
  failed?: boolean;
}

/** LRU inference sessions; active work is never disposed during model switching. */
export class SessionPool<T extends Releasable> {
  readonly #entries = new Map<string, Entry<T>>();
  #trimming = Promise.resolve();
  async use<R>(
    key: string,
    maximum: number,
    create: () => Promise<T>,
    run: (session: T) => Promise<R>,
  ): Promise<R> {
    let entry = this.#entries.get(key);
    if (entry) this.#entries.delete(key);
    else {
      entry = { pending: Promise.resolve().then(create), active: 0 };
      const current = entry;
      entry.pending = entry.pending.catch((error: unknown) => {
        if (this.#entries.get(key) === current) this.#entries.delete(key);
        throw error;
      });
    }
    this.#entries.set(key, entry);
    entry.active++;
    try {
      return await run(await entry.pending);
    } catch (error) {
      entry.failed = true;
      if (this.#entries.get(key) === entry) this.#entries.delete(key);
      throw error;
    } finally {
      entry.active--;
      if (entry.failed && !entry.active) {
        try {
          await (await entry.pending).release();
        } catch {
          /* Preserve the original inference error. */
        }
      }
      this.#trimming = this.#trimming.then(async () => {
        for (const [id, candidate] of this.#entries) {
          if (this.#entries.size <= maximum) break;
          if (candidate.active) continue;
          this.#entries.delete(id);
          try {
            await (await candidate.pending).release();
          } catch {
            /* Best-effort disposal. */
          }
        }
      });
      await this.#trimming;
    }
  }
}
