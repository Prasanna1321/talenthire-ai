// Belongs in: frontend/src/pages/auth/VerifyOtp.jsx
// Phase 2: 6-digit OTP entry, used both right after registration
// (purpose=email_verification) and as step 2 of forgot-password
// (purpose=password_reset, though ForgotPassword.jsx has its own inline
// OTP + new-password step — this page is specifically the post-register flow).
import { useState } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext.jsx'
import { sendOtpRequest } from '../../api/authApi.js'
import { ErrorBanner } from '../../components/Misc.jsx'

export default function VerifyOtp() {
  const { verifyOtp } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const email = searchParams.get('email') || ''

  const [otp, setOtp] = useState('')
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [resending, setResending] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const user = await verifyOtp(email, otp, 'email_verification')
      navigate(`/${user.role}/dashboard`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Verification failed. Please check the code and try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleResend = async () => {
    setError('')
    setInfo('')
    setResending(true)
    try {
      await sendOtpRequest({ email, purpose: 'email_verification' })
      setInfo('A new code has been sent to your email.')
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not resend the code. Please try again shortly.')
    } finally {
      setResending(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <Link to="/" className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-600 text-lg font-bold text-white">
            TH
          </Link>
          <h1 className="text-2xl font-bold text-slate-900">Verify your email</h1>
          <p className="mt-1 text-sm text-slate-500">
            We sent a 6-digit code to <span className="font-medium">{email}</span>
          </p>
        </div>

        <form onSubmit={handleSubmit} className="card space-y-4">
          <ErrorBanner message={error} />
          {info && (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
              {info}
            </div>
          )}

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Verification code</label>
            <input
              type="text"
              inputMode="numeric"
              maxLength={6}
              required
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
              className="input-field text-center text-2xl tracking-[0.5em]"
              placeholder="------"
            />
          </div>

          <button type="submit" disabled={submitting || otp.length !== 6} className="btn-primary w-full">
            {submitting ? 'Verifying...' : 'Verify & Continue'}
          </button>

          <button
            type="button"
            onClick={handleResend}
            disabled={resending}
            className="w-full text-center text-sm font-medium text-brand-600 hover:underline disabled:opacity-50"
          >
            {resending ? 'Sending...' : "Didn't get a code? Resend"}
          </button>
        </form>
      </div>
    </div>
  )
}
