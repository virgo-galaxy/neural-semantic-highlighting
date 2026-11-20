def format_details(name, count)
  escaped = "Quoted: \"hello\"\nPath: C:\\documents\\raw"
  message = "Hello #{name.upcase}: #{count + 1} documents 🌌"
  raw = %q{A literal #{expression}, # comment text and \path}
  words = %W[Overview #{name} Components]
  pattern = %r{\A[a-z]+/#{Regexp.escape(name)}\z}i

  [escaped, message, raw, words.join(", "), pattern.source].join("\n")
end

puts format_details("Virgo", 42)
