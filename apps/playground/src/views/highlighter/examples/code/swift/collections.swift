struct TaskItem {
    let title: String
    let completed: Bool
    let priority: Int
}

func visibleTitles(in tasks: [TaskItem], minimumPriority: Int) -> [String] {
    tasks
        .filter { !$0.completed && $0.priority >= minimumPriority }
        .sorted { left, right in left.priority > right.priority }
        .map(\.title)
}

let priorities = ["Docs": 2, "Design": 4, "Cloud": 3]
let summary = priorities
    .sorted { $0.key < $1.key }
    .map { "\($0.key): \($0.value)" }
    .joined(separator: ", ")
