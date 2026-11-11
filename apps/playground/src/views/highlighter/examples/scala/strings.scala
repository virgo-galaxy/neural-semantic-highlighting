def report(name: String, count: Int, ratio: Double): String =
  val escaped = "Quoted: \"hello\"\nPath: C:\\documents\\raw"
  val summary = s"Hello, $name! ${count + 1} documents 🌌"
  val formatted = f"Progress: $ratio%.2f%%"
  val payload = s"""
    |{ "title": "$name", "count": $count }
    |// This is string content, with ${name.length} characters.
    |""".stripMargin
  List(escaped, summary, formatted, payload).mkString("\n")
