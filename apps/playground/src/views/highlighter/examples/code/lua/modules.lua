local M = {}
local separator <const> = "/"

function M.join(parts)
  return table.concat(parts, separator)
end

function M.read(path)
  local file <close> = assert(io.open(path, "r"))
  return file:read("*a")
end

function M.map(values, transform)
  local output = {}
  for index, value in ipairs(values) do
    output[index] = transform(value)
  end
  return output
end

return M
