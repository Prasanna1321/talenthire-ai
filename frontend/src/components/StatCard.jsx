// Belongs in: frontend/src/components/StatCard.jsx
export default function StatCard({ label, value, accent = 'brand' }) {
  const accentMap = {
    brand: 'text-brand-600 bg-brand-50',
    green: 'text-emerald-600 bg-emerald-50',
    amber: 'text-amber-600 bg-amber-50',
    rose: 'text-rose-600 bg-rose-50',
  }

  return (
    <div className="card">
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className={`mt-2 inline-block rounded-lg px-2 py-1 text-2xl font-bold ${accentMap[accent]}`}>
        {value ?? '—'}
      </p>
    </div>
  )
}
