import { useMemo, useState } from "react";

const filters = ["all", "active", "done"];

export function TaskBoard({ initialTasks = [], onOpenTask }) {
  const [tasks, setTasks] = useState(initialTasks);
  const [filter, setFilter] = useState("all");

  const visibleTasks = useMemo(() => {
    if (filter === "all") {
      return tasks;
    }

    return tasks.filter((task) => task.status === filter);
  }, [filter, tasks]);

  function markDone(taskId) {
    setTasks((currentTasks) =>
      currentTasks.map((task) => (task.id === taskId ? { ...task, status: "done" } : task)),
    );
  }

  return (
    <section aria-label="Task board">
      <header>
        <h2>Tasks</h2>

        <select
          value={filter}
          aria-label="Filter tasks"
          onChange={(event) => setFilter(event.currentTarget.value)}
        >
          {filters.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
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
              <button type="button" onClick={() => markDone(task.id)}>
                Mark done
              </button>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
