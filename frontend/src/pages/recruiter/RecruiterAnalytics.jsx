// Belongs in: frontend/src/pages/recruiter/RecruiterAnalytics.jsx
import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import DashboardLayout from '../../components/DashboardLayout.jsx'
import StatCard from '../../components/StatCard.jsx'
import { LoadingSpinner, ErrorBanner } from '../../components/Misc.jsx'
import { recruiterAnalytics } from '../../api/dashboardApi.js'

export default function RecruiterAnalytics() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    recruiterAnalytics()
      .then((res) => setData(res.data))
      .catch(() => setError('Could not load analytics.'))
      .finally(() => setLoading(false))
  }, [])

  const skillChartData = (data?.top_matched_skills || []).map((skill, idx) => ({
    skill,
    // Weight decays for display purposes since we only return a ranked list
    rank: (data.top_matched_skills.length - idx),
  }))

  return (
    <DashboardLayout role="recruiter">
      <h1 className="mb-1 text-2xl font-bold text-slate-900">Recruiter Analytics</h1>
      <p className="mb-6 text-sm text-slate-500">Hiring funnel metrics across all of your job postings.</p>

      <ErrorBanner message={error} />
      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Jobs Posted" value={data?.total_jobs_posted} accent="brand" />
            <StatCard label="Total Applications" value={data?.total_applications} accent="amber" />
            <StatCard label="Interviews Conducted" value={data?.total_interviews_conducted} accent="green" />
            <StatCard
              label="Avg. Candidate Score"
              value={data?.average_candidate_score ?? '—'}
              accent="green"
            />
          </div>

          {skillChartData.length > 0 && (
            <div className="card mt-8">
              <h3 className="mb-4 font-semibold text-slate-800">Most In-Demand Skills (Your Postings)</h3>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={skillChartData} layout="vertical" margin={{ left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" hide />
                  <YAxis dataKey="skill" type="category" width={140} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="rank" fill="#2f56f5" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </DashboardLayout>
  )
}
