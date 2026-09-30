// Belongs in: frontend/src/pages/candidate/CandidateDashboard.jsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import DashboardLayout from '../../components/DashboardLayout.jsx'
import StatCard from '../../components/StatCard.jsx'
import { LoadingSpinner, ErrorBanner } from '../../components/Misc.jsx'
import { candidateDashboard } from '../../api/dashboardApi.js'

export default function CandidateDashboard() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    candidateDashboard()
      .then((res) => setStats(res.data))
      .catch(() => setError('Could not load dashboard data.'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <DashboardLayout role="candidate">
      <h1 className="mb-1 text-2xl font-bold text-slate-900">
        Welcome back{stats ? `, ${stats.full_name.split(' ')[0]}` : ''} 👋
      </h1>
      <p className="mb-6 text-sm text-slate-500">Here's a snapshot of your interview preparation journey.</p>

      <ErrorBanner message={error} />
      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Resumes Uploaded" value={stats?.total_resumes_uploaded} accent="brand" />
            <StatCard label="Applications Sent" value={stats?.total_applications} accent="amber" />
            <StatCard label="Interviews Taken" value={stats?.total_interviews_taken} accent="green" />
            <StatCard label="Completed" value={stats?.completed_interviews} accent="green" />
          </div>

          <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-3">
            <Link to="/candidate/resume" className="card transition hover:shadow-md">
              <h3 className="font-semibold text-slate-800">📄 Upload Resume</h3>
              <p className="mt-1 text-sm text-slate-500">
                Let our AI parse, classify, and extract skills from your resume.
              </p>
            </Link>
            <Link to="/candidate/jobs" className="card transition hover:shadow-md">
              <h3 className="font-semibold text-slate-800">💼 Browse Jobs</h3>
              <p className="mt-1 text-sm text-slate-500">See AI-recommended roles based on your skills.</p>
            </Link>
            <Link to="/candidate/interview" className="card transition hover:shadow-md">
              <h3 className="font-semibold text-slate-800">🎤 Start Mock Interview</h3>
              <p className="mt-1 text-sm text-slate-500">Practice with AI-generated questions and get feedback.</p>
            </Link>
          </div>
        </>
      )}
    </DashboardLayout>
  )
}
