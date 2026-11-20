# Fenced code

## Python

```python
from pathlib import Path

folder = Path("./examples")
for source in folder.glob("*.md"):
    print(source.name)
```

## Shell

```sh
function greet() {
  printf 'Hello, %s!\n' "$1"
}
greet "source preview"
```

## Unregistered language

```example-language
This body remains original code text.
No language is guessed from its contents.
```
