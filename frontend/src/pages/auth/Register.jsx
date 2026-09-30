// Belongs in: frontend/src/pages/auth/Register.jsx
// PHASE 1 CHANGE: reads a `?role=candidate` or `?role=recruiter` query
// param (set by the Home Page's "Get Started" modal) to preselect the
// role tab. Falls back to "candidate" if absent/invalid.
//
// The "Admin" tab is intentionally hidden from the normal public flow
// (Get Started only ever links to ?role=candidate or ?role=recruiter),
// per the requirement that admin should not be a normal public
// registration option. It still works if someone deep-links directly to
// /register?role=admin (e.g. the project owner setting up a test admin
// account) — a full separate /admin/login + approval workflow is a
// later phase.
import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext.jsx'
import { ErrorBanner } from '../../components/Misc.jsx'

const VALID_ROLES = ['candidate', 'recruiter', 'admin']

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const requestedRole = searchParams.get('role')
  const initialRole = VALID_ROLES.includes(requestedRole) ? requestedRole : 'candidate'
  // Only offer the Admin tab if the page was reached with ?role=admin explicitly.
  const visibleRoles = requestedRole === 'admin' ? ['candidate', 'recruiter', 'admin'] : ['candidate', 'recruiter']

  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    role: initialRole,
    company_name: '',
    phone: '',
    location: '',
  })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await register(form)
      // PHASE 2: registration only sends an OTP now — verification happens on a separate page
      navigate(`/verify-otp?email=${encodeURIComponent(form.email)}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <Link to="/" className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-600 text-lg font-bold text-white">
            TH
          </Link>
          <h1 className="text-2xl font-bold text-slate-900">Create your account</h1>
        </div>

        <form onSubmit={handleSubmit} className="card space-y-4">
          <ErrorBanner message={error} />

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">I am a</label>
            <div className={`grid gap-2 ${visibleRoles.length === 3 ? 'grid-cols-3' : 'grid-cols-2'}`}>
              {visibleRoles.map((r) => (
                <button
                  type="button"
                  key={r}
                  onClick={() => setForm({ ...form, role: r })}
                  className={`rounded-lg border px-3 py-2 text-sm font-medium capitalize transition ${
                    form.role === r
                      ? 'border-brand-500 bg-brand-50 text-brand-700'
                      : 'border-slate-300 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Full name</label>
            <input name="full_name" required value={form.full_name} onChange={handleChange} className="input-field" />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Email</label>
            <input type="email" name="email" required value={form.email} onChange={handleChange} className="input-field" />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Password</label>
            <input
              type="password"
              name="password"
              required
              minLength={8}
              value={form.password}
              onChange={handleChange}
              className="input-field"
            />
          </div>

          {form.role === 'recruiter' && (
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Company name</label>
              <input
                name="company_name"
                required
                value={form.company_name}
                onChange={handleChange}
                className="input-field"
              />
            </div>
          )}

          {form.role === 'candidate' && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Phone</label>
                <input name="phone" value={form.phone} onChange={handleChange} className="input-field" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Location</label>
                <input name="location" value={form.location} onChange={handleChange} className="input-field" />
              </div>
            </div>
          )}

          <button type="submit" disabled={submitting} className="btn-primary w-full">
            {submitting ? 'Creating account...' : 'Create account'}
          </button>

          <p className="text-center text-sm text-slate-500">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-brand-600 hover:underline">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  )
}