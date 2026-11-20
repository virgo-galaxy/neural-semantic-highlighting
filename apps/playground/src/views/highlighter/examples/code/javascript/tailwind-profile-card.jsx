export function ProfileCard({ name, role, avatarUrl, online = false, skills = [] }) {
  const presenceClass = online ? "bg-emerald-500 ring-emerald-100" : "bg-slate-300 ring-slate-100";

  return (
    <article className="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:shadow-md dark:border-slate-800 dark:bg-slate-950">
      <div className="flex items-start gap-4">
        <div className="relative shrink-0">
          <img
            src={avatarUrl}
            alt=""
            className="h-14 w-14 rounded-full object-cover ring-2 ring-white dark:ring-slate-900"
          />

          <span
            className={`absolute -bottom-1 -right-1 h-4 w-4 rounded-full ring-4 ${presenceClass}`}
            aria-label={online ? "Online" : "Offline"}
          />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h2 className="truncate text-lg font-semibold text-slate-900 dark:text-slate-100">
                {name}
              </h2>

              <p className="truncate text-sm text-slate-500 dark:text-slate-400">{role}</p>
            </div>

            <button
              type="button"
              className="rounded-lg px-3 py-1.5 text-sm font-medium text-blue-600 transition hover:bg-blue-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:text-blue-400 dark:hover:bg-blue-950/50"
            >
              View
            </button>
          </div>

          {skills.length > 0 && (
            <ul className="mt-4 flex flex-wrap gap-2">
              {skills.map((skill) => (
                <li
                  key={skill}
                  className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                >
                  {skill}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </article>
  );
}
