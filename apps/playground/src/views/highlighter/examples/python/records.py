from dataclasses import dataclass


@dataclass(frozen=True)
class Note:
    title: str
    tags: tuple[str, ...] = ()

    def summary(self, limit: int = 40) -> str:
        return self.title[:limit].strip()


def published_titles(notes: list[Note]) -> list[str]:
    return [note.summary() for note in notes if "public" in note.tags]
