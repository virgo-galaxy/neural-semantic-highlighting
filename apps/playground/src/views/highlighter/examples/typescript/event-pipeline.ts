type DomainEvent =
  | { type: "user.created"; userId: string; email: string }
  | { type: "user.deleted"; userId: string }
  | { type: "order.paid"; orderId: string; amount: number };

type EventOf<T extends DomainEvent["type"]> = Extract<DomainEvent, { type: T }>;

type Handler<T extends DomainEvent["type"]> = (event: EventOf<T>) => void | Promise<void>;

class EventPipeline {
  private readonly handlers = new Map<string, Set<Handler<DomainEvent["type"]>>>();

  on<T extends DomainEvent["type"]>(type: T, handler: Handler<T>): () => void {
    const listeners = this.handlers.get(type) ?? new Set();
    listeners.add(handler as Handler<DomainEvent["type"]>);
    this.handlers.set(type, listeners);

    return () => {
      listeners.delete(handler as Handler<DomainEvent["type"]>);
    };
  }

  async emit(event: DomainEvent): Promise<void> {
    const listeners = this.handlers.get(event.type);

    if (!listeners?.size) {
      return;
    }

    await Promise.all([...listeners].map((handler) => handler(event)));
  }
}

const pipeline = new EventPipeline();

pipeline.on("user.created", async ({ userId, email }) => {
  const domain = email.match(/@([^@]+)$/)?.[1] ?? "unknown";
  console.log(`Created ${userId} on ${domain}`);
});

void pipeline.emit({
  type: "user.created",
  userId: crypto.randomUUID(),
  email: "developer@example.com",
});
