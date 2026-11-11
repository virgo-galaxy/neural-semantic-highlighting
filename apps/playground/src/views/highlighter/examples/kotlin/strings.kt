fun message(name: String, count: Int): String {
    val path = "C:\\Documents\\Kotlin"
    val details = """
        Hello, $name 🌌
        You have ${count + 1} documents.
        Regex text stays inside a string: [a-z]+\.[0-9]+
    """.trimIndent()
    val metadata = $$"""
        { "$schema": "document", "title": "$$name", "count": $${count + 1} }
    """.trimIndent()
    return "$path\n$details\n$metadata"
}
