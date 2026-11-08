"""Original small Python grammar curriculum; never collect Golden/Playground."""
from pathlib import Path
import hashlib
import json
from training.shared.spec import PackSpec, REPOSITORY, file_hash

TEMPLATES={
 'functions':'''def {name}(items: list[int], scale: int = {n}) -> list[int]:
    """Transform an original sequence."""
    result = []
    for value in items:
        result.append(value * scale)
    return result
''',
 'classes':'''class {cls}:
    def __init__(self, value: str):
        self.value = value
    @property
    def label(self) -> str:
        return self.value.upper()
''',
 'async':'''async def {name}(client, *, limit={n}):
    async with client.session() as session:
        async for item in session.stream():
            if item.ready:
                yield await item.read(limit)
''',
 'generators':'''def {name}(start={n}):
    while start > 0:
        yield start
        start -= 1
    yield from range(3)
''',
 'decorators':'''from functools import lru_cache
@lru_cache(maxsize={n})
def {name}(value: str) -> str:
    return value.strip().lower()
''',
 'patterns':'''def {name}(message):
    match message:
        case {{"kind": "ready", "value": value}} if value:
            return value
        case [first, *rest]:
            return first, rest
        case _:
            return None
''',
 'comprehensions':'''def {name}(items):
    selected = {{item.key: item.value for item in items if item.enabled}}
    unique = {{entry for entry in selected.values()}}
    return sorted(unique), [x * {n} for x in unique]
''',
 'scope':'''def {name}(items, len):
    def count(values):
        return len(values)
    return count(items)
class {cls}:
    len = {n}
    def size(self):
        return len(self.items)
''',
 'closures':'''def {name}(initial={n}):
    count = initial
    def advance(step=1):
        nonlocal count
        count += step
        return count
    return advance
''',
 'imports':'''import os.path as paths
from pathlib import Path
from collections import defaultdict as groups
def {name}(root: str):
    location = Path(paths.join(root, "data"))
    return location.read_text(encoding="utf-8")
''',
 'generic-alias':'''type {cls}[T] = dict[str, list[T]]
def {name}[T](value: T) -> list[T]:
    return [value]
''',
 'generic-class':'''class {cls}[T: str = str]:
    def __init__(self, item: T):
        self.item = item
    def fetch(self) -> T:
        return self.item
''',
 'variadic-types':'''type {cls}[*Ts] = tuple[*Ts]
def {name}[**P, R](fn: object, *args, **kwargs):
    return fn(*args, **kwargs)
''',
 'formatted-strings':'''def {name}(user, amount={n}):
    title = f"Hello {{user.name!s}}, balance {{amount:,.2f}}"
    return title, rf"{{user.id}}/\\w+", b"ready"
''',
 'template-strings':'''def {name}(user):
    template = t"<strong>{{user}}</strong>"
    message = f"{{user!r}}" " joined literal"
    return template, message
''',
 'exceptions':'''def {name}(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except (OSError, ValueError) as error:
        raise RuntimeError("failed") from error
    finally:
        print("finished")
''',
 'operators':'''def {name}(items):
    if (size := len(items)) >= {n} and items is not None:
        head, *tail = items
        return lambda value: (value << 1) | size
    return None
''',
 'unicode':'''# 原始文本 🌌
def {name}(名字: str):
    文本 = f"你好 {{名字}} 🚀"
    return 文本, {n}
''',
 'long-strings':'''def {name}():
    text = """An original documentation paragraph.
{paragraph}
"""
    return text
''',
 'raw-strings':'''# Literals preserve their prefixes and delimiters.
{name} = (r"\\w+\\s*", b'byte-data', 0xFF, 1.2e-3, 2j)
assert {name}[0] != ""
''',
 'continuations':'''def {name}(value):
    result = value + \\
        {n}
    return result
''',
}

def main():
    destination=PackSpec.open('python').dataset_root/'sources/curriculum-v1'
    files={}
    for family,template in TEMPLATES.items():
        for index in range(18):
            name=['transform','collect','render','load','resolve','prepare'][index%6]+f'_{index}'
            source=template.format(name=name,cls=['Record','Cache','Store'][index%3]+str(index),n=index+2,
                paragraph=('This bounded passage documents values, paths, and multiline behavior. '* (4+index%12)).rstrip())
            if index%6==1:source=source.replace('\n','\r\n')
            relative=f'{family}/{index:02}.py'
            files[relative]=source.encode('utf-8')
    files['LICENSE']=b'Original curriculum authored for the private neural-semantic-highlighting project. No public distribution or additional license grant.\n'
    destination.mkdir(parents=True,exist_ok=True)
    for name,raw in files.items():
        path=destination/name
        if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve existing curriculum; create a new revision')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    lock={'format':'nsh-python-original-curriculum-v1','generatorHash':file_hash(Path(__file__)),
          'files':{name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()}}
    path=destination/'source.lock.json'
    if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Existing curriculum lock changed')
    path.write_text(json.dumps(lock,indent=2)+'\n')
    print(destination, len(files)-1,'original source files')

if __name__=='__main__':main()
