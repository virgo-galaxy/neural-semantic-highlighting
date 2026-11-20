data class TaskItem(
    val title: String,
    val completed: Boolean,
    val priority: Int,
)

fun visibleTitles(tasks: List<TaskItem>, minimumPriority: Int): List<String> =
    tasks.asSequence()
        .filter { !it.completed && it.priority >= minimumPriority }
        .sortedByDescending { it.priority }
        .map(TaskItem::title)
        .toList()

fun summarize(priorities: Map<String, Int>): String =
    priorities.entries
        .sortedBy { it.key }
        .joinToString(", ") { (name, priority) -> "$name: $priority" }
