local function createStore(initial)
  local value = initial
  return {
    get = function() return value end,
    update = function(transform)
      value = transform(value)
      return value
    end,
  }
end

local store = createStore(10)
local ok, result = pcall(store.update, function(current)
  return current * 2
end)
print(ok, result, store.get())
