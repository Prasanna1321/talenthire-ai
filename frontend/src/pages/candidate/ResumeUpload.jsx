// Belongs in: frontend/src/pages/candidate/ResumeUpload.jsx
// PHASE 4: shows the real, explainable TalentHire AI ATS Compatibility
// Score (with a per-category breakdown) instead of any classification
// label, supports the resume-versioning consistency-check confirmation
// flow, and lists resume version history.
import { useEffect, useRef, useState } from 'react'
import DashboardLayout from '../../components/DashboardLayout.jsx'
import { ErrorBanner, LoadingSpinner, EmptyState } from '../../components/Misc.jsx'
import { uploadResume, resumeHistory, getJobRecommendations } from '../../api/resumesApi.js'

const BREAKDOWN_LABELS = {
  skills_match: { label: 'Skills Match', max: 30 },
  experience: { label: 'Experience', max: 20 },
  education: { label: 'Education', max: 10 },
  projects: { label: 'Projects', max: 15 },
  keywords: { label: 'Keywords', max: 10 },
  completeness: { label: 'Completeness', max: 10 },
  formatting: { label: 'Formatting', max: 5 },
}

function ATSBreakdownBar({ label, score, max }) {
  const pct = Math.min(100, (score / max) * 100)
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="text-slate-600">{label}</span>
        <span className="font-medium text-slate-700">{score.toFixed(1)} / {max}</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-brand-500" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default function ResumeUpload() {
  const [resumes, setResumes] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [pendingWarning, setPendingWarning] = useState(null) // { warning, file }
  const fileInputRef = useRef(null)

  const loadData = async () => {
    try {
      const [resumesRes, recRes] = await Promise.all([resumeHistory(), getJobRecommendations()])
      setResumes(resumesRes.data)
      setRecommendations(recRes.data)
    } catch {
      setError('Could not load resume data.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const doUpload = async (file, force) => {
    setError('')
    setUploading(true)
    try {
      const res = await uploadResume(file, force)
      if (res.data.requires_confirmation) {
        setPendingWarning({ warning: res.data.warning, file })
      } else {
        setPendingWarning(null)
        await loadData()
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Resume upload failed. Please upload a PDF file.')
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleFileChange = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    await doUpload(file, false)
  }

  const currentResume = resumes.find((r) => r.is_current)

  return (
    <DashboardLayout role="candidate">
      <h1 className="mb-1 text-2xl font-bold text-slate-900">Resume Upload</h1>
      <p className="mb-6 text-sm text-slate-500">
        Upload a PDF resume — our AI parses it, extracts your skills, and calculates your ATS Compatibility Score.
      </p>

      <ErrorBanner message={error} />

      {pendingWarning && (
        <div className="card mb-6 border border-amber-200 bg-amber-50">
          <p className="mb-3 text-sm text-amber-800">{pendingWarning.warning}</p>
          <div className="flex gap-3">
            <button
              onClick={() => doUpload(pendingWarning.file, true)}
              disabled={uploading}
              className="btn-primary text-sm"
            >
              Verify & Use New Resume
            </button>
            <button
              onClick={() => setPendingWarning(null)}
              className="btn-secondary text-sm"
            >
              Keep Current Resume
            </button>
          </div>
        </div>
      )}

      <div className="card mb-8">
        <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-300 px-6 py-10 text-center">
          <p className="mb-3 text-sm text-slate-500">PDF resumes only, up to 10MB</p>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
            className="hidden"
            id="resume-input"
          />
          <label htmlFor="resume-input" className="btn-primary cursor-pointer">
            {uploading ? 'Uploading & analyzing...' : 'Choose PDF file'}
          </label>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
          {currentResume && (
            <div className="card mb-8">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-800">TalentHire AI ATS Compatibility Score</h2>
                <span className="text-3xl font-bold text-brand-600">
                  {currentResume.ats_score?.toFixed(0) ?? '—'} <span className="text-base text-slate-400">/ 100</span>
                </span>
              </div>
              {currentResume.ats_breakdown && (
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  {Object.entries(currentResume.ats_breakdown).map(([key, score]) => {
                    const meta = BREAKDOWN_LABELS[key]
                    if (!meta) return null
                    return <ATSBreakdownBar key={key} label={meta.label} score={score} max={meta.max} />
                  })}
                </div>
              )}
              <div className="mt-4 flex flex-wrap gap-1.5">
                {(currentResume.extracted_skills || []).map((s) => (
                  <span key={s} className="badge bg-slate-100 text-slate-600">{s}</span>
                ))}
              </div>
            </div>
          )}

          <h2 className="mb-3 text-lg font-semibold text-slate-800">Resume History</h2>
          {resumes.length === 0 ? (
            <EmptyState message="No resumes uploaded yet." />
          ) : (
            <div className="mb-8 space-y-3">
              {resumes.map((r) => (
                <div key={r.resume_id} className="card">
                  <div className="flex items-center justify-between">
                    <p className="font-medium text-slate-800">
                      {r.original_filename} <span className="text-xs text-slate-400">v{r.version_number}</span>
                    </p>
                    <div className="flex items-center gap-2">
                      {r.is_current && <span className="badge bg-emerald-50 text-emerald-700">Current</span>}
                      <span className="badge bg-brand-50 text-brand-700">{r.ats_score?.toFixed(0) ?? '—'} / 100</span>
                    </div>
                  </div>
                  <p className="mt-1 text-xs text-slate-400">
                    Uploaded {new Date(r.uploaded_at).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          )}

          <h2 className="mb-3 text-lg font-semibold text-slate-800">AI-Recommended Jobs</h2>
          {recommendations.length === 0 ? (
            <EmptyState message="Upload a resume to get personalized job recommendations." />
          ) : (
            <div className="space-y-3">
              {recommendations.map((job) => (
                <div key={job.job_id} className="card flex items-center justify-between">
                  <div>
                    <p className="font-medium text-slate-800">{job.title}</p>
                    <p className="text-sm text-slate-500">{job.company_name}</p>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {job.matched_skills.map((s) => (
                        <span key={s} className="badge bg-emerald-50 text-emerald-700">{s}</span>
                      ))}
                    </div>
                  </div>
                  <span className="badge bg-brand-100 text-brand-700">{job.match_score}% match</span>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </DashboardLayout>
  )
}
