// Belongs in: frontend/src/pages/recruiter/RecruiterDashboard.jsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import DashboardLayout from '../../components/DashboardLayout.jsx'
import StatCard from '../../components/StatCard.jsx'
import { LoadingSpinner, ErrorBanner } from '../../components/Misc.jsx'
import { recruiterDashboard, getRecruiterProfile } from '../../api/dashboardApi.js'
import PendingApproval from './PendingApproval.jsx'

export default function RecruiterDashboard() {
  const [stats, setStats] = useState(null)
  const [profile, setProfile] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([recruiterDashboard(), getRecruiterProfile()])
      .then(([dashRes, profileRes]) => {
        setStats(dashRes.data)
        setProfile(profileRes.data)
      })
      .catch(() => setError('Could not load dashboard data.'))
      .finally(() => setLoading(false))
  }, [])

  if (!loading && profile && profile.status !== 'approved') {
    return <PendingApproval status={profile.status} />
  }

  return (
    <DashboardLayout role="recruiter">
      <h1 className="mb-1 text-2xl font-bold text-slate-900">
        {stats ? stats.company_name : 'Recruiter'} Dashboard
      </h1>
      <p className="mb-6 text-sm text-slate-500">Manage job postings and review AI-assisted candidate evaluations.</p>

      <ErrorBanner message={error} />
      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Jobs Posted" value={stats?.total_jobs_posted} accent="brand" />
            <StatCard label="Open Jobs" value={stats?.open_jobs} accent="green" />
            <StatCard label="Applications Received" value={stats?.total_applications_received} accent="amber" />
            <StatCard label="Shortlisted Candidates" value={stats?.shortlisted_candidates} accent="green" />
          </div>

          <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-2">
            <Link to="/recruiter/jobs" className="card transition hover:shadow-md">
              <h3 className="font-semibold text-slate-800">💼 Manage Jobs</h3>
              <p className="mt-1 text-sm text-slate-500">Post new roles and review applicants with AI match scores.</p>
            </Link>
            <Link to="/recruiter/analytics" className="card transition hover:shadow-md">
              <h3 className="font-semibold text-slate-800">📊 Analytics</h3>
              <p className="mt-1 text-sm text-slate-500">See hiring funnel metrics and candidate score trends.</p>
            </Link>
          </div>
        </>
      )}
    </DashboardLayout>
  )
}
