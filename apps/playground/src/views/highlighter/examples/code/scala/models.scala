case class Document(id: Long, title: String, views: Int)

enum LoadState:
  case Idle
  case Ready(documents: List[Document])
  case Failed(message: String)

def describe(state: LoadState): String = state match
  case LoadState.Idle => "Waiting"
  case LoadState.Ready(documents) => s"${documents.size} documents"
  case LoadState.Failed(message) => s"Failed: $message"
