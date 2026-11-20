# 原始 Unicode、字符串和注释 🌌
name = "Virgo"
greeting = f"Hello, {name}!"
template = t"<strong>{name}</strong>"
pattern = r"\b[a-z]+\d*\b"
payload = b"ready\x00"
message = "A short " "joined message"

print(greeting, pattern, payload)
