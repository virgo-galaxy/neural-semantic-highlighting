-- Long brackets preserve literal newlines and backslashes.
local template = [==[
<section class="card">
  <h1>${title} is literal text</h1>
  <!-- [[nested-looking]] and ]=] are ordinary text -->
</section>
C:\workspace\sources
]==]

--[=[ A long comment can contain "quotes" and -- markers. ]=]
local title = "Lua 🌌"
local slug = title:gsub("%s+", "-"):lower()
print(string.format("%s: %d bytes\n", slug, #template))
