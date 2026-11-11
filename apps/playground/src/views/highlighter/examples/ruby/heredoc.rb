def render_report(title, views)
  summary = <<~REPORT
    # Document report
    Title: #{title}
    Views: #{views + 1}
    Unicode: 星空 🌌
  REPORT

  literal = <<'TEXT'
#{this_is_literal_text}
C:\documents\raw
TEXT

  [summary.strip, literal.strip].join("\n\n")
end

puts render_report("Getting Started", 42)
