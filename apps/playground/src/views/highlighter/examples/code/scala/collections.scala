case class Task(title: String, priority: Int, completed: Boolean)

def pendingTitles(tasks: List[Task]): List[String] =
  for
    task <- tasks
    if !task.completed
  yield task.title.trim

def countByPriority(tasks: List[Task]): Map[Int, Int] =
  tasks.groupMapReduce(_.priority)(_ => 1)(_ + _)

val totals = List("open" -> 4, "done" -> 8)
val labels = totals.map { case (label, count) => s"$label: $count" }
