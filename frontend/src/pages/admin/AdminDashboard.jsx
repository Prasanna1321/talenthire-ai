// Belongs in: frontend/src/pages/admin/AdminDashboard.jsx
import { useEffect, useState } from 'react'
import DashboardLayout from '../../components/DashboardLayout.jsx'
import StatCard from '../../components/StatCard.jsx'
import { LoadingSpinner, ErrorBanner } from '../../components/Misc.jsx'
import { adminDashboard } from '../../api/dashboardApi.js'

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    adminDashboard()
      .then((res) => setStats(res.data))
      .catch(() => setError('Could not load system stats.'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <DashboardLayout role="admin">
      <h1 className="mb-1 text-2xl font-bold text-slate-900">Admin Dashboard</h1>
      <p className="mb-6 text-sm text-slate-500">System-wide overview of TalentHire AI.</p>

      <ErrorBanner message={error} />
      {loading ? (
        <LoadingSpinner />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Total Users" value={stats?.total_users} accent="brand" />
          <StatCard label="Candidates" value={stats?.total_candidates} accent="green" />
          <StatCard label="Recruiters" value={stats?.total_recruiters} accent="amber" />
          <StatCard label="Jobs Posted" value={stats?.total_jobs} accent="brand" />
          <StatCard label="Applications" value={stats?.total_applications} accent="amber" />
          <StatCard label="Resumes Uploaded" value={stats?.total_resumes_uploaded} accent="green" />
          <StatCard label="Interview Sessions" value={stats?.total_interview_sessions} accent="brand" />
        </div>
      )}
    </DashboardLayout>
  )
}
