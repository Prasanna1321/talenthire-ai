// Belongs in: frontend/src/pages/auth/ForgotPassword.jsx
// Phase 2: 3-step forgot-password flow: enter email -> enter OTP + new
// password -> success -> back to login. All in one page via a step state.
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { forgotPasswordRequest, resetPasswordRequest } from '../../api/authApi.js'
import { ErrorBanner } from '../../components/Misc.jsx'

const STEP = { EMAIL: 'email', RESET: 'reset', DONE: 'done' }

export default function ForgotPassword() {
  const navigate = useNavigate()
  const [step, setStep] = useState(STEP.EMAIL)
  const [email, setEmail] = useState('')
  const [otp, setOtp] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSendCode = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await forgotPasswordRequest({ email })
      setStep(STEP.RESET)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not send the reset code. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleReset = async (e) => {
    e.preventDefault()
    setError('')
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    setSubmitting(true)
    try {
      await resetPasswordRequest({ email, otp, new_password: newPassword })
      setStep(STEP.DONE)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not reset your password. Please check the code and try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <Link to="/" className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-600 text-lg font-bold text-white">
            TH
          </Link>
          <h1 className="text-2xl font-bold text-slate-900">Reset your password</h1>
        </div>

        {step === STEP.EMAIL && (
          <form onSubmit={handleSendCode} className="card space-y-4">
            <ErrorBanner message={error} />
            <p className="text-sm text-slate-500">Enter your account email — we'll send a reset code.</p>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Email</label>
              <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="input-field" />
            </div>
            <button type="submit" disabled={submitting} className="btn-primary w-full">
              {submitting ? 'Sending...' : 'Send Reset Code'}
            </button>
          </form>
        )}

        {step === STEP.RESET && (
          <form onSubmit={handleReset} className="card space-y-4">
            <ErrorBanner message={error} />
            <p className="text-sm text-slate-500">Enter the code sent to <span className="font-medium">{email}</span> and your new password.</p>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Reset code</label>
              <input
                type="text"
                inputMode="numeric"
                maxLength={6}
                required
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                className="input-field text-center text-xl tracking-[0.4em]"
                placeholder="------"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">New password</label>
              <input type="password" required minLength={8} value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="input-field" />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Confirm new password</label>
              <input type="password" required minLength={8} value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="input-field" />
            </div>
            <button type="submit" disabled={submitting || otp.length !== 6} className="btn-primary w-full">
              {submitting ? 'Resetting...' : 'Reset Password'}
            </button>
          </form>
        )}

        {step === STEP.DONE && (
          <div className="card space-y-4 text-center">
            <h2 className="text-lg font-semibold text-emerald-700">Password Reset Successful</h2>
            <p className="text-sm text-slate-500">You can now log in with your new password.</p>
            <button onClick={() => navigate('/login')} className="btn-primary w-full">
              Back to Login
            </button>
          </div>
        )}

        {step !== STEP.DONE && (
          <p className="mt-4 text-center text-sm text-slate-500">
            Remembered your password? <Link to="/login" className="font-medium text-brand-600 hover:underline">Sign in</Link>
          </p>
        )}
      </div>
    </div>
  )
}
