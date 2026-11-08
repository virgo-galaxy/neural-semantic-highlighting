"""Standard-library parser for independently authored marked fixtures."""
import re

def unmark(marked: str) -> dict:
    source, spans, cursor, units = "", [], 0, 0
    for match in re.finditer(r"⟦([^|]+)\|([\s\S]*?)⟧", marked):
        gap = marked[cursor:match.start()]
        if gap.strip():
            raise ValueError("Golden source has an unmarked source gap")
        source += gap
        units += len(gap.encode("utf-16-le")) // 2
        role, *modifiers = match[1].split("+")
        start = units
        source += match[2]
        units += len(match[2].encode("utf-16-le")) // 2
        span = {"start": start, "end": units, "tokenType": role}
        if modifiers:
            span["modifiers"] = modifiers
        spans.append(span)
        cursor = match.end()
    if marked[cursor:].strip():
        raise ValueError("Golden source has an unmarked source tail")
    return {"source": source + marked[cursor:], "spans": spans}

