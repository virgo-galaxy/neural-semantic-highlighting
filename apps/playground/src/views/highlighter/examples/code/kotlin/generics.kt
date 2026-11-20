interface Identified<Key> {
    val id: Key
}

class Repository<Key, Item : Identified<Key>> {
    private val items = mutableMapOf<Key, Item>()

    fun save(item: Item) {
        items[item.id] = item
    }

    fun find(id: Key): Item? = items[id]

    fun <Result> map(transform: (Item) -> Result): List<Result> =
        items.values.map(transform)
}

interface LogSink {
    fun log(message: String)
}

context(logger: LogSink)
fun announce(title: String) {
    logger.log("Document: $title")
}
