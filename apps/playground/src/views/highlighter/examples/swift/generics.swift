protocol Identified {
    associatedtype ID: Hashable
    var id: ID { get }
}

struct Repository<Item: Identified> {
    private var items: [Item.ID: Item] = [:]

    mutating func save(_ item: Item) {
        items[item.id] = item
    }

    func find(_ id: Item.ID) -> Item? {
        items[id]
    }
}

struct Document: Identified {
    let id: String
    var title: String
}

var repository = Repository<Document>()
repository.save(Document(id: "intro", title: "Getting started"))
