// Belongs in: frontend/src/pages/recruiter/JobManagement.jsx
import { useEffect, useState } from 'react'
import DashboardLayout from '../../components/DashboardLayout.jsx'
import { ErrorBanner, LoadingSpinner, EmptyState, StatusBadge } from '../../components/Misc.jsx'
import { listMyJobs, createJob, jobCandidatesDetailed, updateApplicationStatus } from '../../api/jobsApi.js'
import { generateQuestions } from '../../api/interviewsApi.js'

const EMPTY_JOB = {
  title: '',
  description: '',
  required_skills: '',
  experience_level: 'entry',
  location: '',
  job_type: 'full-time',
}

const APPLICATION_STATUSES = [
  'applied', 'shortlisted', 'interview_scheduled', 'interview_completed', 'selected', 'rejected',
]

export default function JobManagement() {
  const [jobs, setJobs] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(EMPTY_JOB)
  const [selectedJob, setSelectedJob] = useState(null)
  const [applicants, setApplicants] = useState([])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [generatingQuestions, setGeneratingQuestions] = useState(false)

  const loadJobs = () => {
    setLoading(true)
    listMyJobs()
      .then((res) => setJobs(res.data))
      .catch(() => setError('Could not load your job postings.'))
      .finally(() => setLoading(false))
  }

  useEffect(loadJobs, [])

  const handleCreateJob = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      await createJob({
        ...form,
        required_skills: form.required_skills.split(',').map((s) => s.trim()).filter(Boolean),
      })
      setForm(EMPTY_JOB)
      setShowForm(false)
      loadJobs()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not create job posting.')
    } finally {
      setSubmitting(false)
    }
  }

  const viewApplicants = async (job) => {
    setSelectedJob(job)
    setError('')
    try {
      const res = await jobCandidatesDetailed(job.job_id)
      setApplicants(res.data)
    } catch {
      setError('Could not load applicants for this job.')
    }
  }

  const handleGenerateQuestions = async (job) => {
    setGeneratingQuestions(true)
    setError('')
    setSuccess('')
    try {
      await generateQuestions({ job_id: job.job_id, num_questions: 5, difficulty: 'mixed' })
      setSuccess(`5 AI interview questions generated for "${job.title}".`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not generate interview questions.')
    } finally {
      setGeneratingQuestions(false)
    }
  }

  const handleStatusChange = async (applicationId, status) => {
    try {
      await updateApplicationStatus(applicationId, status)
      setApplicants((prev) => prev.map((a) => (a.application_id === applicationId ? { ...a, status } : a)))
    } catch {
      setError('Could not update application status.')
    }
  }

  return (
    <DashboardLayout role="recruiter">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Manage Jobs</h1>
          <p className="text-sm text-slate-500">Post roles, generate AI interview questions, review applicants.</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary">
          {showForm ? 'Cancel' : '+ Post New Job'}
        </button>
      </div>

      <ErrorBanner message={error} />
      {success && (
        <div className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {success}
        </div>
      )}

      {showForm && (
        <form onSubmit={handleCreateJob} className="card mb-8 space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Job Title</label>
            <input
              required
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="input-field"
              placeholder="e.g. Gen AI Engineer Intern"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Description</label>
            <textarea
              required
              rows={3}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="input-field"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Required Skills (comma-separated)</label>
            <input
              required
              value={form.required_skills}
              onChange={(e) => setForm({ ...form, required_skills: e.target.value })}
              className="input-field"
              placeholder="Python, LLM, Prompt Engineering, FastAPI"
            />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Experience</label>
              <select
                value={form.experience_level}
                onChange={(e) => setForm({ ...form, experience_level: e.target.value })}
                className="input-field"
              >
                <option value="entry">Entry</option>
                <option value="mid">Mid</option>
                <option value="senior">Senior</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Location</label>
              <input
                value={form.location}
                onChange={(e) => setForm({ ...form, location: e.target.value })}
                className="input-field"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Job Type</label>
              <input
                value={form.job_type}
                onChange={(e) => setForm({ ...form, job_type: e.target.value })}
                className="input-field"
              />
            </div>
          </div>
          <button type="submit" disabled={submitting} className="btn-primary">
            {submitting ? 'Posting...' : 'Post Job'}
          </button>
        </form>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Your Jobs</h2>
          {loading ? (
            <LoadingSpinner />
          ) : jobs.length === 0 ? (
            <EmptyState message="No jobs posted yet." />
          ) : (
            <div className="space-y-3">
              {jobs.map((job) => (
                <div key={job.job_id} className="card">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold text-slate-800">{job.title}</h3>
                      <p className="text-xs text-slate-400">{job.location} · {job.status}</p>
                    </div>
                    <StatusBadge status={job.status} />
                  </div>
                  <div className="mt-3 flex gap-2">
                    <button onClick={() => viewApplicants(job)} className="btn-secondary text-xs">
                      View Applicants
                    </button>
                    <button
                      onClick={() => handleGenerateQuestions(job)}
                      disabled={generatingQuestions}
                      className="btn-secondary text-xs"
                    >
                      {generatingQuestions ? 'Generating...' : '✨ Generate AI Questions'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
            {selectedJob ? `Applicants for "${selectedJob.title}"` : 'Applicants'}
          </h2>
          {!selectedJob ? (
            <EmptyState message="Select a job on the left to view applicants." />
          ) : applicants.length === 0 ? (
            <EmptyState message="No applicants yet for this job." />
          ) : (
            <div className="space-y-3">
              {applicants.map((app) => (
                <div key={app.application_id} className="card">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-slate-700">{app.full_name}</p>
                      <p className="text-xs text-slate-400">{app.email}</p>
                    </div>
                    <span className="badge bg-brand-100 text-brand-700">{app.match_score ?? 0}% match</span>
                  </div>
                  <div className="mt-2 grid grid-cols-3 gap-2 text-center text-xs">
                    <div className="rounded bg-slate-50 py-1.5">
                      <p className="text-slate-400">ATS</p>
                      <p className="font-semibold text-slate-700">{app.ats_score?.toFixed(0) ?? '—'}</p>
                    </div>
                    <div className="rounded bg-slate-50 py-1.5">
                      <p className="text-slate-400">Aptitude</p>
                      <p className="font-semibold text-slate-700">{app.aptitude_percentage?.toFixed(0) ?? '—'}%</p>
                    </div>
                    <div className="rounded bg-slate-50 py-1.5">
                      <p className="text-slate-400">Interview</p>
                      <p className="font-semibold text-slate-700">{app.interview_score?.toFixed(0) ?? '—'}</p>
                    </div>
                  </div>
                  {app.missing_skills?.length > 0 && (
                    <p className="mt-2 text-xs text-rose-600">Missing: {app.missing_skills.join(', ')}</p>
                  )}
                  <select
                    value={app.status}
                    onChange={(e) => handleStatusChange(app.application_id, e.target.value)}
                    className="input-field mt-2 text-xs"
                  >
                    {APPLICATION_STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {s.replace(/_/g, ' ')}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}
