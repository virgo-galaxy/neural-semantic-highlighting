-- A small Lua module
local function greet(name, punctuation)
  return string.format("Hello, %s%s", name, punctuation or "!")
end

local names = {"Ada", "Linus", "Grace"}
for index, name in ipairs(names) do
  print(index, greet(name))
end
