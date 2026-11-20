class AsyncCache {
  #entries = new Map();

  constructor(ttlMs = 30_000) {
    this.ttlMs = ttlMs;
  }

  async get(key, loader) {
    const cached = this.#entries.get(key);

    if (cached && cached.expiresAt > Date.now()) {
      return cached.value;
    }

    const value = await loader();
    this.#entries.set(key, {
      value,
      expiresAt: Date.now() + this.ttlMs,
    });

    return value;
  }
}

const cache = new AsyncCache();

const user = await cache.get("user:42", async () => {
  const response = await fetch("https://api.example.com/users/42");

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json();
});

console.log(user?.name ?? "Anonymous");
