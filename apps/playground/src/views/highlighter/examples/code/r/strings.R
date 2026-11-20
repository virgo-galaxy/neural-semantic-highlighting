format_report <- function(title, total) {
  escaped <- "Quoted: \"hello\"\nPath: C:\\documents\\report"
  template <- r"---[
    # This stays string content.
    { "title": "Document", "pattern": "[a-z]+\\d+" }
    Quotes, $names and ${expressions} are literal R text.
  ]---"
  heading <- sprintf("%s: %d views 🌌", title, total)
  paste(heading, escaped, template, sep = "\n")
}

`display title` <- format_report("星空", 42L)
cat(`display title`)
