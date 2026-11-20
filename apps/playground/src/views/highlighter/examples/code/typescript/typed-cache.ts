interface CacheEntry<T> {
  value: T;
  expiresAt: number;
}

class TypedCache<T> {
  private readonly entries = new Map<string, CacheEntry<T>>();

  constructor(private readonly ttlMs: number) {}

  set(key: string, value: T): void {
    this.entries.set(key, {
      value,
      expiresAt: Date.now() + this.ttlMs,
    });
  }

  get(key: string): T | undefined {
    const entry = this.entries.get(key);

    if (!entry || entry.expiresAt <= Date.now()) {
      this.entries.delete(key);
      return undefined;
    }

    return entry.value;
  }
}

const cache = new TypedCache<number>(30_000);
cache.set("requests", 42);
console.log(cache.get("requests") ?? 0);
