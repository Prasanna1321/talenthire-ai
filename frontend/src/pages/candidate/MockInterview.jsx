// Belongs in: frontend/src/pages/candidate/MockInterview.jsx
// Full Mock Interview module: pick a job -> generate/load questions ->
// start a session -> answer each question (typed, or recorded via the
// browser's MediaRecorder API and sent to the Whisper speech-to-text
// endpoint) -> see the per-answer score -> complete session -> AI feedback.

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DashboardLayout from '../../components/DashboardLayout.jsx'
import { ErrorBanner, LoadingSpinner } from '../../components/Misc.jsx'
import { ScoreBadge } from '../../components/Misc.jsx'
import { listJobs } from '../../api/jobsApi.js'
import {
  listQuestionsForJob,
  startSession,
  submitTextAnswer,
  submitAudioAnswer,
  completeSession,
} from '../../api/interviewsApi.js'

const STAGE = { SELECT_JOB: 'select_job', ANSWERING: 'answering', DONE: 'done' }

export default function MockInterview() {
  const navigate = useNavigate()
  const [stage, setStage] = useState(STAGE.SELECT_JOB)
  const [jobs, setJobs] = useState([])
  const [selectedJobId, setSelectedJobId] = useState('')
  const [questions, setQuestions] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [session, setSession] = useState(null)
  const [typedAnswer, setTypedAnswer] = useState('')
  const [lastScore, setLastScore] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Audio recording state
  const [recorder, setRecorder] = useState(null)
  const [isRecording, setIsRecording] = useState(false)
  const [audioChunks, setAudioChunks] = useState([])

  useEffect(() => {
    listJobs({ status: 'open' }).then((res) => setJobs(res.data)).catch(() => {})
  }, [])

  const handleStart = async () => {
    if (!selectedJobId) {
      setError('Please select a job role to practice for.')
      return
    }
    setError('')
    setLoading(true)
    try {
      let qRes = await listQuestionsForJob(selectedJobId)
      if (qRes.data.length === 0) {
        setError('This job has no interview questions yet. Ask the recruiter to generate them, or pick another job.')
        setLoading(false)
        return
      }
      const sessionRes = await startSession({ job_id: Number(selectedJobId), session_type: 'mock' })
      setQuestions(qRes.data)
      setSession(sessionRes.data)
      setStage(STAGE.ANSWERING)
    } catch (err) {
      const detail = err.response?.data?.detail || 'Could not start the interview session.'
      // PHASE 5 GATE: backend blocks this until the 30-question aptitude test is completed
      if (err.response?.status === 403 && detail.toLowerCase().includes('aptitude')) {
        navigate('/candidate/aptitude-test')
        return
      }
      setError(detail)
    } finally {
      setLoading(false)
    }
  }

  const currentQuestion = questions[currentIndex]

  const handleSubmitText = async () => {
    if (!typedAnswer.trim()) return
    setLoading(true)
    setError('')
    try {
      const res = await submitTextAnswer(session.session_id, {
        session_id: session.session_id,
        question_id: currentQuestion.question_id,
        transcribed_text: typedAnswer,
      })
      setLastScore(res.data)
      setTypedAnswer('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not submit your answer.')
    } finally {
      setLoading(false)
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      const chunks = []
      mediaRecorder.ondataavailable = (e) => chunks.push(e.data)
      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/webm' })
        setLoading(true)
        try {
          const res = await submitAudioAnswer(session.session_id, currentQuestion.question_id, blob)
          setLastScore(res.data)
        } catch (err) {
          setError(err.response?.data?.detail || 'Could not process your recorded answer.')
        } finally {
          setLoading(false)
        }
      }
      mediaRecorder.start()
      setRecorder(mediaRecorder)
      setAudioChunks(chunks)
      setIsRecording(true)
    } catch {
      setError('Microphone access denied. You can type your answer instead.')
    }
  }

  const stopRecording = () => {
    recorder?.stop()
    setIsRecording(false)
  }

  const handleNext = () => {
    setLastScore(null)
    if (currentIndex + 1 < questions.length) {
      setCurrentIndex(currentIndex + 1)
    } else {
      handleFinish()
    }
  }

  const handleFinish = async () => {
    setLoading(true)
    setError('')
    try {
      await completeSession(session.session_id)
      setStage(STAGE.DONE)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not generate your feedback report.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <DashboardLayout role="candidate">
      <h1 className="mb-1 text-2xl font-bold text-slate-900">Mock Interview</h1>
      <p className="mb-6 text-sm text-slate-500">
        Practice with AI-generated questions. Answer by typing or recording your voice.
      </p>

      <ErrorBanner message={error} />

      {stage === STAGE.SELECT_JOB && (
        <div className="card max-w-lg space-y-4">
          <label className="block text-sm font-medium text-slate-700">Select a job role to practice for</label>
          <select
            value={selectedJobId}
            onChange={(e) => setSelectedJobId(e.target.value)}
            className="input-field"
          >
            <option value="">-- Select a job --</option>
            {jobs.map((j) => (
              <option key={j.job_id} value={j.job_id}>
                {j.title}
              </option>
            ))}
          </select>
          <button onClick={handleStart} disabled={loading} className="btn-primary w-full">
            {loading ? 'Starting...' : 'Start Mock Interview'}
          </button>
          <button
            onClick={() => navigate(`/candidate/voice-interview${selectedJobId ? `?job_id=${selectedJobId}` : ''}`)}
            className="btn-secondary w-full text-sm"
          >
            🎙 Try Real-Time AI Voice Interview (Beta)
          </button>
        </div>
      )}

      {stage === STAGE.ANSWERING && currentQuestion && (
        <div className="card max-w-2xl space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>
              Question {currentIndex + 1} of {questions.length}
            </span>
            <span className="badge bg-slate-100 capitalize text-slate-600">
              {currentQuestion.question_type} · {currentQuestion.difficulty}
            </span>
          </div>

          <h2 className="text-lg font-semibold text-slate-800">{currentQuestion.question_text}</h2>

          {!lastScore ? (
            <>
              <textarea
                value={typedAnswer}
                onChange={(e) => setTypedAnswer(e.target.value)}
                rows={5}
                placeholder="Type your answer here..."
                className="input-field"
              />
              <div className="flex gap-3">
                <button onClick={handleSubmitText} disabled={loading} className="btn-primary flex-1">
                  {loading ? 'Evaluating...' : 'Submit Typed Answer'}
                </button>
                {!isRecording ? (
                  <button onClick={startRecording} className="btn-secondary flex-1">
                    🎤 Record Answer
                  </button>
                ) : (
                  <button onClick={stopRecording} className="btn-secondary flex-1 border-rose-300 text-rose-600">
                    ⏹ Stop & Submit
                  </button>
                )}
              </div>
            </>
          ) : (
            <div className="space-y-3">
              <div className="rounded-lg bg-slate-50 p-4">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-600">Overall Score</span>
                  <ScoreBadge score={Number(lastScore.final_score)} />
                </div>
                <div className="grid grid-cols-3 gap-2 text-center text-xs text-slate-500">
                  <div>
                    Relevance
                    <p className="font-semibold text-slate-700">{lastScore.relevance_score}</p>
                  </div>
                  <div>
                    Fluency
                    <p className="font-semibold text-slate-700">{lastScore.fluency_score}</p>
                  </div>
                  <div>
                    Confidence
                    <p className="font-semibold text-slate-700">{lastScore.confidence_score}</p>
                  </div>
                </div>
              </div>
              <button onClick={handleNext} className="btn-primary w-full">
                {currentIndex + 1 < questions.length ? 'Next Question' : 'Finish Interview & Get Feedback'}
              </button>
            </div>
          )}
        </div>
      )}

      {stage === STAGE.DONE && (
        <div className="card max-w-md text-center">
          <h2 className="mb-2 text-xl font-bold text-slate-800">Interview Complete! 🎉</h2>
          <p className="mb-4 text-sm text-slate-500">
            Your AI-generated feedback report is ready.
          </p>
          <button onClick={() => navigate('/candidate/reports')} className="btn-primary w-full">
            View My Feedback Report
          </button>
        </div>
      )}
    </DashboardLayout>
  )
}
