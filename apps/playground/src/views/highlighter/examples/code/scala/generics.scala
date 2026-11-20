trait Identified[Key]:
  def id: Key

class Repository[Key, Item <: Identified[Key]](private val entries: List[Item]):
  def find(id: Key): Option[Item] = entries.find(_.id == id)
  def map[Result](transform: Item => Result): List[Result] =
    entries.map(transform)

type DocumentId = Long
case class Record(id: DocumentId, title: String) extends Identified[DocumentId]

val records = new Repository[DocumentId, Record](List(Record(1L, "Overview")))
val titles = records.map(record => record.title)
