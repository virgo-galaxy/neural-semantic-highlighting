type Group[T] = dict[str, list[T]]


def first[T](items: list[T]) -> T | None:
    return items[0] if items else None


def describe(value: object) -> str:
    match value:
        case {"name": str(name), "active": True}:
            return f"Active: {name}"
        case [head, *tail]:
            return f"Sequence of {len(tail) + 1}: {head!r}"
        case _:
            return "Unknown"
