// Belongs in: frontend/src/pages/candidate/AptitudeTest.jsx
// Phase 5: exactly 30 MCQ aptitude questions, required before the live
// AI video interview (enforced by the backend).
// Correct answers are never sent to the browser until AFTER submission.

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DashboardLayout from '../../components/DashboardLayout.jsx'
import { ErrorBanner, LoadingSpinner } from '../../components/Misc.jsx'
import {
  startAptitudeTest,
  submitAptitudeTest,
} from '../../api/aptitudeApi.js'

export default function AptitudeTest() {
  const navigate = useNavigate()

  const [testId, setTestId] = useState(null)
  const [questions, setQuestions] = useState([])
  const [answers, setAnswers] = useState({})
  const [currentIndex, setCurrentIndex] = useState(0)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  useEffect(() => {
    startAptitudeTest()
      .then((res) => {
        setTestId(res.data.test_id)
        setQuestions(res.data.questions)
      })
      .catch((err) => {
        setError(
          err.response?.data?.detail ||
          'Could not start the aptitude test.'
        )
      })
      .finally(() => setLoading(false))
  }, [])

  const currentQuestion = questions[currentIndex]
  const answeredCount = Object.keys(answers).length

  const selectOption = (questionId, option) => {
    setAnswers((previous) => ({
      ...previous,
      [questionId]: option,
    }))
  }

  const handleSubmit = async () => {
    setSubmitting(true)
    setError('')

    try {
      const payload = {
        test_id: testId,
        answers: Object.entries(answers).map(
          ([question_id, selected_option]) => ({
            question_id: Number(question_id),
            selected_option,
          })
        ),
      }

      const res = await submitAptitudeTest(payload)
      setResult(res.data)
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Could not submit the test.'
      )
    } finally {
      setSubmitting(false)
    }
  }

  // Loading state
  if (loading) {
    return (
      <DashboardLayout role="candidate">
        <LoadingSpinner label="Preparing your aptitude test..." />
      </DashboardLayout>
    )
  }

  // Aptitude result
  if (result) {
    return (
      <DashboardLayout role="candidate">
        <div className="card max-w-md text-center">
          <h2 className="mb-2 text-xl font-bold text-slate-800">
            Aptitude Test Complete
          </h2>

          <p className="mb-4 text-4xl font-bold text-brand-600">
            {result.percentage}%
          </p>

          <p className="mb-4 text-sm text-slate-500">
            {result.score} correct out of {result.total_questions} questions
          </p>

          <button
            onClick={() => navigate('/candidate/voice-interview')}
            className="btn-primary w-full"
          >
            Start Live AI Interview
          </button>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout role="candidate">
      <h1 className="mb-1 text-2xl font-bold text-slate-900">
        Aptitude Test
      </h1>

      <p className="mb-6 text-sm text-slate-500">
        Answer all 30 questions, then submit. Correct answers are graded after submission.
      </p>

      <ErrorBanner message={error} />

      {currentQuestion && (
        <div className="card max-w-2xl space-y-4">

          {/* Question header */}
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>
              Question {currentIndex + 1} of {questions.length}
            </span>

            <span className="badge bg-slate-100 capitalize text-slate-600">
              {currentQuestion.category.replace(/_/g, ' ')}
            </span>
          </div>

          {/* Question */}
          <h2 className="text-lg font-semibold text-slate-800">
            {currentQuestion.question_text}
          </h2>

          {/* Options */}
          <div className="space-y-2">
            {['A', 'B', 'C', 'D'].map((opt) => (
              <button
                key={opt}
                onClick={() =>
                  selectOption(
                    currentQuestion.question_id,
                    opt
                  )
                }
                className={`w-full rounded-lg border px-4 py-3 text-left text-sm transition ${
                  answers[currentQuestion.question_id] === opt
                    ? 'border-brand-500 bg-brand-50 text-brand-700'
                    : 'border-slate-200 text-slate-700 hover:bg-slate-50'
                }`}
              >
                <span className="mr-2 font-semibold">
                  {opt}.
                </span>

                {currentQuestion[
                  `option_${opt.toLowerCase()}`
                ]}
              </button>
            ))}
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-between pt-2">

            <button
              onClick={() =>
                setCurrentIndex(
                  Math.max(0, currentIndex - 1)
                )
              }
              disabled={currentIndex === 0}
              className="btn-secondary text-sm disabled:opacity-40"
            >
              Previous
            </button>

            <span className="text-xs text-slate-400">
              {answeredCount} / {questions.length} answered
            </span>

            {currentIndex + 1 < questions.length ? (
              <button
                onClick={() =>
                  setCurrentIndex(currentIndex + 1)
                }
                className="btn-primary text-sm"
              >
                Next
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={
                  submitting ||
                  answeredCount < questions.length
                }
                className="btn-primary text-sm"
              >
                {submitting
                  ? 'Submitting...'
                  : 'Submit Test'}
              </button>
            )}
          </div>
        </div>
      )}
    </DashboardLayout>
  )
}