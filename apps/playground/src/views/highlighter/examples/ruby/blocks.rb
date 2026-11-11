def make_counter(start = 0)
  count = start
  ->(step = 1) { count += step }
end

def process_values(values, **options, &transform)
  values.filter_map do |value|
    next if value.nil?
    transform.call(value, **options)
  end
end

counter = make_counter(10)
result = process_values([1, nil, 3], scale: 2) do |value, scale:|
  value * scale
end

puts "#{counter.call}: #{result.inspect}"
