// Belongs in: frontend/src/pages/candidate/InterviewReports.jsx
import { useEffect, useState } from 'react'
import DashboardLayout from '../../components/DashboardLayout.jsx'
import { ErrorBanner, LoadingSpinner, EmptyState, ScoreBadge, StatusBadge } from '../../components/Misc.jsx'
import { mySessions, getReport, downloadReportPdf } from '../../api/interviewsApi.js'

export default function InterviewReports() {
  const [sessions, setSessions] = useState([])
  const [selectedReport, setSelectedReport] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [reportLoading, setReportLoading] = useState(false)
  const [downloading, setDownloading] = useState(false)

  useEffect(() => {
    mySessions()
      .then((res) => setSessions(res.data))
      .catch(() => setError('Could not load interview history.'))
      .finally(() => setLoading(false))
  }, [])

  const viewReport = async (sessionId) => {
    setReportLoading(true)
    setError('')
    try {
      const res = await getReport(sessionId)
      setSelectedReport(res.data)
    } catch {
      setError('Could not load this report.')
    } finally {
      setReportLoading(false)
    }
  }

  const handleDownloadPdf = async (sessionId) => {
    setDownloading(true)
    setError('')
    try {
      const res = await downloadReportPdf(sessionId)
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const link = document.createElement('a')
      link.href = url
      link.download = `talenthire_report_session_${sessionId}.pdf`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      setError('Could not generate the PDF report.')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <DashboardLayout role="candidate">
      <h1 className="mb-1 text-2xl font-bold text-slate-900">Interview Reports</h1>
      <p className="mb-6 text-sm text-slate-500">Review your past mock interview sessions and AI feedback.</p>

      <ErrorBanner message={error} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Sessions</h2>
          {loading ? (
            <LoadingSpinner />
          ) : sessions.length === 0 ? (
            <EmptyState message="No interview sessions yet." />
          ) : (
            <div className="space-y-2">
              {sessions.map((s) => (
                <button
                  key={s.session_id}
                  onClick={() => viewReport(s.session_id)}
                  className={`card w-full text-left transition hover:shadow-md ${
                    selectedReport?.session.session_id === s.session_id ? 'ring-2 ring-brand-500' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-slate-700">Session #{s.session_id}</span>
                    <StatusBadge status={s.status} />
                  </div>
                  <p className="mt-1 text-xs text-slate-400">{new Date(s.started_at).toLocaleString()}</p>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="lg:col-span-2">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Report Detail</h2>
          {reportLoading ? (
            <LoadingSpinner />
          ) : !selectedReport ? (
            <EmptyState message="Select a session on the left to view its full report." />
          ) : (
            <div className="space-y-4">
              {/* Summary Header & PDF download */}
              <div className="card border-l-4 border-l-brand-600">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-slate-900">Session #{selectedReport.session.session_id} Report</h3>
                    <p className="text-xs text-slate-500">
                      Started: {new Date(selectedReport.session.started_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    {selectedReport.average_score != null && (
                      <ScoreBadge score={selectedReport.average_score} />
                    )}
                    <button
                      onClick={() => handleDownloadPdf(selectedReport.session.session_id)}
                      disabled={downloading}
                      className="btn-secondary text-xs"
                    >
                      {downloading ? 'Generating...' : '📄 Download PDF Report'}
                    </button>
                  </div>
                </div>
              </div>

              {/* Aptitude Performance Card */}
              {selectedReport.aptitude && (
                <div className="card">
                  <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2">
                    <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                      <span>🧠</span> Aptitude Assessment Performance
                    </h3>
                    <span className="badge bg-purple-50 text-purple-700 font-semibold text-xs">
                      {selectedReport.aptitude.percentage}%
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-center sm:grid-cols-3">
                    <div className="rounded-lg bg-slate-50 p-3">
                      <p className="text-xs text-slate-500">Score</p>
                      <p className="text-lg font-bold text-slate-800">
                        {selectedReport.aptitude.score} / {selectedReport.aptitude.total_questions}
                      </p>
                    </div>
                    <div className="rounded-lg bg-slate-50 p-3">
                      <p className="text-xs text-slate-500">Percentage</p>
                      <p className="text-lg font-bold text-slate-800">
                        {selectedReport.aptitude.percentage}%
                      </p>
                    </div>
                    <div className="col-span-2 sm:col-span-1 rounded-lg bg-slate-50 p-3">
                      <p className="text-xs text-slate-500">Status</p>
                      <p className="text-lg font-bold text-emerald-600">Completed</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Observable Visual Indicators Card */}
              {selectedReport.visual_metrics && (
                <div className="card">
                  <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2">
                    <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                      <span>👁️</span> Observable Visual Indicators
                    </h3>
                    <span className="text-[10px] uppercase font-bold text-slate-400">Measurable Metrics</span>
                  </div>
                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div className="rounded-xl bg-blue-50/60 p-3">
                      <p className="text-xs font-medium text-slate-600">Face Visibility</p>
                      <p className="mt-1 text-base font-bold text-blue-700">
                        {selectedReport.visual_metrics.face_visibility != null ? `${selectedReport.visual_metrics.face_visibility}%` : 'N/A'}
                      </p>
                    </div>
                    <div className="rounded-xl bg-indigo-50/60 p-3">
                      <p className="text-xs font-medium text-slate-600">Camera Alignment</p>
                      <p className="mt-1 text-base font-bold text-indigo-700">
                        {selectedReport.visual_metrics.camera_orientation != null ? `${selectedReport.visual_metrics.camera_orientation}%` : 'N/A'}
                      </p>
                    </div>
                    <div className="rounded-xl bg-teal-50/60 p-3">
                      <p className="text-xs font-medium text-slate-600">Posture Stability</p>
                      <p className="mt-1 text-base font-bold text-teal-700">
                        {selectedReport.visual_metrics.posture_consistency != null ? `${selectedReport.visual_metrics.posture_consistency}%` : 'N/A'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* AI Feedback Card */}
              {selectedReport.feedback && (
                <div className="card space-y-3">
                  <h3 className="font-semibold text-slate-800 border-b border-slate-100 pb-2 flex items-center gap-2">
                    <span>🤖</span> AI Interviewer Evaluation & Feedback
                  </h3>
                  <div>
                    <p className="font-semibold text-emerald-700 text-xs uppercase tracking-wider">Strengths</p>
                    <p className="mt-1 text-sm text-slate-600">{selectedReport.feedback.strengths}</p>
                  </div>
                  <div>
                    <p className="font-semibold text-amber-700 text-xs uppercase tracking-wider">Areas to Improve</p>
                    <p className="mt-1 text-sm text-slate-600">{selectedReport.feedback.areas_to_improve}</p>
                  </div>
                  <div>
                    <p className="font-semibold text-slate-700 text-xs uppercase tracking-wider">Detailed Feedback</p>
                    <p className="mt-1 text-sm text-slate-600">{selectedReport.feedback.detailed_feedback}</p>
                  </div>
                  {selectedReport.feedback.overall_rating != null && (
                    <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
                      <p className="font-semibold text-sm text-slate-700">Overall Rating:</p>
                      <span className="badge bg-brand-100 text-brand-700 font-bold">
                        {selectedReport.feedback.overall_rating} / 10
                      </span>
                    </div>
                  )}
                </div>
              )}

              {/* Answer-by-Answer Breakdown */}
              <div>
                <h3 className="mb-2 font-semibold text-slate-800">Answer-by-Answer Breakdown</h3>
                {selectedReport.answers.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">No stored individual answer records for this session.</p>
                ) : (
                  <div className="space-y-2">
                    {selectedReport.answers.map((a, idx) => {
                      const score = selectedReport.scores.find((s) => s.answer_id === a.answer_id)
                      return (
                        <div key={a.answer_id} className="card">
                          <div className="mb-1 flex items-center justify-between">
                            <span className="text-xs font-medium text-slate-400">Answer {idx + 1}</span>
                            <ScoreBadge score={score ? Number(score.final_score) : null} />
                          </div>
                          <p className="text-sm text-slate-600">{a.transcribed_text}</p>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}
