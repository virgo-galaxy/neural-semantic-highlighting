local function valuesUntil(limit)
  return coroutine.wrap(function()
    local value = 0
    repeat
      value = value + 1
      local done = value >= limit
      coroutine.yield(value)
    until done
  end)
end

local total = 0
for value in valuesUntil(8) do
  if value % 2 == 0 then
    total = total + value
  end
end
print(total)
