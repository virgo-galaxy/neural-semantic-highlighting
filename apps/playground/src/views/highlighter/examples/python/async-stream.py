import asyncio


async def changes(queue: asyncio.Queue):
    while True:
        event = await queue.get()
        try:
            if event is None:
                break
            yield event
        finally:
            queue.task_done()


async def consume(queue: asyncio.Queue) -> None:
    async for event in changes(queue):
        print(f"Received {event!r}")
