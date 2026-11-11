@JvmInline
value class DocumentId(val value: String)

data class Document(
    val id: DocumentId,
    val title: String,
    val tags: Set<String> = emptySet(),
)

sealed interface LoadState {
    data object Idle : LoadState
    data class Ready(val documents: List<Document>) : LoadState
    data class Failed(val message: String) : LoadState
}

fun describe(state: LoadState): String = when (state) {
    LoadState.Idle -> "Ready to load"
    is LoadState.Ready -> "${state.documents.size} documents"
    is LoadState.Failed -> state.message
}
