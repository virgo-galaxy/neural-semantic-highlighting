trait Logger:
  def write(message: String): Unit

given consoleLogger: Logger with
  def write(message: String): Unit = println(message)

def publish(title: String)(using logger: Logger): Unit =
  logger.write(s"Published: $title")

extension (title: String)
  def slug: String = title.trim.toLowerCase.replace(' ', '-')

object Identifiers:
  opaque type DocumentId = Long
  def create(value: Long): DocumentId = value

publish("Getting Started".slug)
