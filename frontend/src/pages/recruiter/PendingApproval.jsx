// Belongs in: frontend/src/pages/recruiter/PendingApproval.jsx
// Phase 3: shown instead of the recruiter dashboard when the recruiter's
// account status isn't 'approved' yet. The backend independently enforces
// this on every job-management endpoint (see require_approved_recruiter
// in core/dependencies.py) — this page is just the corresponding UX.
import DashboardLayout from '../../components/DashboardLayout.jsx'

const STATUS_COPY = {
  pending: {
    title: 'Your recruiter account is pending approval',
    body: "An admin needs to review and approve your account before you can post jobs or manage candidates. You'll get an email once that happens — usually within a day.",
    color: 'text-amber-600 bg-amber-50 border-amber-200',
  },
  rejected: {
    title: 'Your recruiter application was not approved',
    body: 'If you believe this was a mistake, please contact TalentHire AI support.',
    color: 'text-rose-600 bg-rose-50 border-rose-200',
  },
  suspended: {
    title: 'Your recruiter account has been suspended',
    body: 'Please contact TalentHire AI support for more information.',
    color: 'text-rose-600 bg-rose-50 border-rose-200',
  },
}

export default function PendingApproval({ status = 'pending' }) {
  const copy = STATUS_COPY[status] || STATUS_COPY.pending

  return (
    <DashboardLayout role="recruiter">
      <div className={`card max-w-lg border ${copy.color}`}>
        <h1 className="mb-2 text-xl font-bold">{copy.title}</h1>
        <p className="text-sm">{copy.body}</p>
      </div>
    </DashboardLayout>
  )
}
