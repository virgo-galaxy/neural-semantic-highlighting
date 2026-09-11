import { useMemo, useState } from "react";

type TaskStatus = "todo" | "doing" | "done";

interface Task {
  id: string;
  title: string;
  status: TaskStatus;
  assignee?: {
    name: string;
    avatarUrl?: string;
  };
}

interface TaskBoardProps {
  initialTasks: readonly Task[];
  onOpenTask?: (task: Task) => void;
}

export function TaskBoard({ initialTasks, onOpenTask }: TaskBoardProps) {
  const [tasks, setTasks] = useState(() => [...initialTasks]);
  const [filter, setFilter] = useState<TaskStatus | "all">("all");

  const visibleTasks = useMemo(() => {
    if (filter === "all") {
      return tasks;
    }

    return tasks.filter((task) => task.status === filter);
  }, [filter, tasks]);

  function moveTask(id: string, status: TaskStatus): void {
    setTasks((current) =>
      current.map((task) =>
        task.id === id
          ? {
              ...task,
              status,
            }
          : task,
      ),
    );
  }

  return (
    <section aria-label="Task board">
      <header>
        <h2>Tasks</h2>

        <select
          value={filter}
          aria-label="Filter tasks"
          onChange={(event) => setFilter(event.currentTarget.value as TaskStatus | "all")}
        >
          <option value="all">All</option>
          <option value="todo">Todo</option>
          <option value="doing">Doing</option>
          <option value="done">Done</option>
        </select>
      </header>

      <ul>
        {visibleTasks.map((task) => (
          <li key={task.id}>
            <button type="button" onClick={() => onOpenTask?.(task)}>
              <strong>{task.title}</strong>
              <span>{task.assignee?.name ?? "Unassigned"}</span>
            </button>

            {task.status !== "done" && (
              <button type="button" onClick={() => moveTask(task.id, "done")}>
                Mark done
              </button>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
