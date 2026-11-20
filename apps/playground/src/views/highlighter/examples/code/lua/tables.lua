local Counter = {}
Counter.__index = Counter

function Counter.new(label)
  return setmetatable({ label = label, count = 0 }, Counter)
end

function Counter:add(amount)
  self.count = self.count + amount
  return self.count
end

local counter = Counter.new("Visits")
counter:add(5)
print(counter.label, counter.count)
