class EventBus {
  #listeners = new Map();

  on(type, listener) {
    const listeners = this.#listeners.get(type) ?? new Set();
    listeners.add(listener);
    this.#listeners.set(type, listeners);

    return () => {
      listeners.delete(listener);
    };
  }

  async emit(type, payload) {
    const listeners = this.#listeners.get(type);

    if (!listeners?.size) {
      return;
    }

    await Promise.all([...listeners].map((listener) => listener(payload)));
  }
}

const bus = new EventBus();

bus.on("user.created", ({ id, email }) => {
  const domain = email.match(/@([^@]+)$/)?.[1] ?? "unknown";
  console.log(`Created ${id} on ${domain}`);
});

void bus.emit("user.created", {
  id: crypto.randomUUID(),
  email: "developer@example.com",
});
