fun greeting(name: String, excited: Boolean = false): String {
    val title = name.trim().ifEmpty { "friend" }
    return "Hello, $title" + if (excited) "!" else "."
}

fun main() {
    val names = listOf("Virgo", "星空 🌌", "Kotlin")
    for (name in names) {
        println(greeting(name = name, excited = true))
    }
}
