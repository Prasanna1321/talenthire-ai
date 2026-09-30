// Belongs in: frontend/src/pages/candidate/JobBrowse.jsx
import { useEffect, useState } from 'react'
import DashboardLayout from '../../components/DashboardLayout.jsx'
import { ErrorBanner, LoadingSpinner, EmptyState } from '../../components/Misc.jsx'
import { listJobs } from '../../api/jobsApi.js'
import { applyToJob } from '../../api/jobsApi.js'
import { listMyResumes } from '../../api/resumesApi.js'

export default function JobBrowse() {
  const [jobs, setJobs] = useState([])
  const [resumes, setResumes] = useState([])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(true)
  const [applyingId, setApplyingId] = useState(null)

  useEffect(() => {
    Promise.all([listJobs({ status: 'open' }), listMyResumes()])
      .then(([jobsRes, resumesRes]) => {
        setJobs(jobsRes.data)
        setResumes(resumesRes.data)
      })
      .catch(() => setError('Could not load job listings.'))
      .finally(() => setLoading(false))
  }, [])

  const handleApply = async (jobId) => {
    setError('')
    setSuccess('')
    setApplyingId(jobId)
    try {
      const latestResumeId = resumes[0]?.resume_id
      await applyToJob({ job_id: jobId, resume_id: latestResumeId })
      setSuccess('Application submitted successfully!')
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not submit application.')
    } finally {
      setApplyingId(null)
    }
  }

  return (
    <DashboardLayout role="candidate">
      <h1 className="mb-1 text-2xl font-bold text-slate-900">Browse Jobs</h1>
      <p className="mb-6 text-sm text-slate-500">Open positions posted by recruiters on TalentHire AI.</p>

      <ErrorBanner message={error} />
      {success && (
        <div className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {success}
        </div>
      )}

      {loading ? (
        <LoadingSpinner />
      ) : jobs.length === 0 ? (
        <EmptyState message="No open positions right now. Check back soon!" />
      ) : (
        <div className="space-y-4">
          {jobs.map((job) => (
            <div key={job.job_id} className="card">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-slate-800">{job.title}</h3>
                  <p className="text-sm text-slate-500">
                    {job.location || 'Remote'} · {job.job_type} · <span className="capitalize">{job.experience_level}</span>
                  </p>
                </div>
                <button
                  onClick={() => handleApply(job.job_id)}
                  disabled={applyingId === job.job_id}
                  className="btn-primary text-sm"
                >
                  {applyingId === job.job_id ? 'Applying...' : 'Apply Now'}
                </button>
              </div>
              <p className="mt-3 text-sm text-slate-600">{job.description}</p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                {job.required_skills.map((s) => (
                  <span key={s} className="badge bg-slate-100 text-slate-600">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </DashboardLayout>
  )
}
