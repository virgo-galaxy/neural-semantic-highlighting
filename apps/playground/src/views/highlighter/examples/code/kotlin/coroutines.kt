import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow

suspend fun loadDocument(id: String, fetch: suspend (String) -> String): String =
    coroutineScope {
        delay(10)
        fetch(id).trim()
    }

fun documentEvents(names: List<String>): Flow<String> = flow {
    for ((index, name) in names.withIndex()) {
        emit("${index + 1}: $name")
        delay(5)
    }
}
