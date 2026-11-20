def greeting(name, excited: false)
  title = name.strip
  suffix = excited ? "!" : "."
  "Hello, #{title}#{suffix}"
end

names = ["Virgo", "星空 🌌", "Ruby"]
names.each do |name|
  puts greeting(name, excited: true)
end
