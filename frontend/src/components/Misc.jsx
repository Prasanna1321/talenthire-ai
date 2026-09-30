// Belongs in: frontend/src/components/Misc.jsx
// Small shared UI primitives used across several pages.

export function ScoreBadge({ score }) {
  if (score === null || score === undefined) return <span className="badge bg-slate-100 text-slate-500">—</span>

  let colorClasses = 'bg-rose-100 text-rose-700'
  if (score >= 75) colorClasses = 'bg-emerald-100 text-emerald-700'
  else if (score >= 50) colorClasses = 'bg-amber-100 text-amber-700'

  return <span className={`badge ${colorClasses}`}>{score.toFixed(1)}</span>
}

export function StatusBadge({ status }) {
  const colorMap = {
    open: 'bg-emerald-100 text-emerald-700',
    closed: 'bg-slate-200 text-slate-600',
    draft: 'bg-amber-100 text-amber-700',
    applied: 'bg-slate-100 text-slate-600',
    shortlisted: 'bg-brand-100 text-brand-700',
    interview_scheduled: 'bg-amber-100 text-amber-700',
    interview_completed: 'bg-sky-100 text-sky-700',
    selected: 'bg-emerald-100 text-emerald-700',
    rejected: 'bg-rose-100 text-rose-700',
    completed: 'bg-emerald-100 text-emerald-700',
    in_progress: 'bg-amber-100 text-amber-700',
  }

  return (
    <span className={`badge capitalize ${colorMap[status] || 'bg-slate-100 text-slate-600'}`}>
      {status?.replace(/_/g, ' ')}
    </span>
  )
}

export function LoadingSpinner({ label = 'Loading...' }) {
  return (
    <div className="flex items-center justify-center gap-2 py-12 text-sm text-slate-500">
      <svg className="h-4 w-4 animate-spin text-brand-500" viewBox="0 0 24 24" fill="none">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
      </svg>
      {label}
    </div>
  )
}

export function ErrorBanner({ message }) {
  if (!message) return null
  return (
    <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
      {message}
    </div>
  )
}

export function EmptyState({ message }) {
  return <div className="card text-center text-sm text-slate-500">{message}</div>
}
