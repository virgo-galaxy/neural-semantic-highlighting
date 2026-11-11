def greeting(name: String, excited: Boolean = false): String =
  val title = name.trim
  val suffix = if excited then "!" else "."
  s"Hello, $title$suffix"

@main def hello(): Unit =
  val names = List("Virgo", "星空 🌌", "Scala")
  names.foreach { name =>
    println(greeting(name, excited = true))
  }
