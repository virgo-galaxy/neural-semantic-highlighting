interface ProfileCardProps {
  name: string;
  role: string;
  avatarUrl: string;
  online?: boolean;
  skills: readonly string[];
}

export function ProfileCard({ name, role, avatarUrl, online = false, skills }: ProfileCardProps) {
  const presenceClass = online ? "bg-emerald-500 ring-emerald-100" : "bg-slate-300 ring-slate-100";

  return (
    <article className="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg dark:border-slate-800 dark:bg-slate-950">
      <div className="flex items-start gap-4">
        <div className="relative shrink-0">
          <img
            src={avatarUrl}
            alt=""
            className="h-14 w-14 rounded-full object-cover ring-2 ring-white dark:ring-slate-900"
          />

          <span
            className={`absolute -bottom-0.5 -right-0.5 h-4 w-4 rounded-full ring-4 ${presenceClass}`}
            aria-label={online ? "Online" : "Offline"}
          />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <h2 className="truncate text-base font-semibold text-slate-950 dark:text-white">
                {name}
              </h2>
              <p className="truncate text-sm text-slate-500 dark:text-slate-400">{role}</p>
            </div>

            <button
              type="button"
              className="rounded-lg bg-slate-950 px-3 py-2 text-xs font-medium text-white transition hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:bg-white dark:text-slate-950"
            >
              View profile
            </button>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {skills.map((skill) => (
              <span
                key={skill}
                className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-200"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      </div>
    </article>
  );
}
