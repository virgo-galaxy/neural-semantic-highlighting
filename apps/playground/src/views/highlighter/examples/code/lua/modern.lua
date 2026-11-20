-- Lua 5.5 explicit globals and named varargs
global none
global print, table
global<const> LIMIT = 10

local function collect(...items)
  local values <const> = {...}
  for index = 1, #values do
    if index > LIMIT then break end
    print(index, values[index])
  end
  return table.concat(values, ", "), items
end

print(collect("one", "two", "three"))
