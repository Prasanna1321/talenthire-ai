// Belongs in: frontend/src/pages/admin/RecruiterApprovals.jsx
// Phase 3: admin approves/rejects/suspends/activates recruiter accounts.
import { useEffect, useState } from 'react'
import DashboardLayout from '../../components/DashboardLayout.jsx'
import { ErrorBanner, LoadingSpinner, EmptyState } from '../../components/Misc.jsx'
import { listRecruiters, approveRecruiter, rejectRecruiter, suspendRecruiter, activateRecruiter } from '../../api/dashboardApi.js'

const TABS = ['pending', 'approved', 'rejected', 'suspended']

export default function RecruiterApprovals() {
  const [tab, setTab] = useState('pending')
  const [recruiters, setRecruiters] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actingOn, setActingOn] = useState(null)

  const load = (status) => {
    setLoading(true)
    listRecruiters(status)
      .then((res) => setRecruiters(res.data))
      .catch(() => setError('Could not load recruiters.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => load(tab), [tab])

  const handleAction = async (action, recruiterId) => {
    setActingOn(recruiterId)
    setError('')
    try {
      const actionFn = { approve: approveRecruiter, reject: rejectRecruiter, suspend: suspendRecruiter, activate: activateRecruiter }[action]
      await actionFn(recruiterId)
      load(tab)
    } catch {
      setError(`Could not ${action} this recruiter.`)
    } finally {
      setActingOn(null)
    }
  }

  return (
    <DashboardLayout role="admin">
      <h1 className="mb-1 text-2xl font-bold text-slate-900">Recruiter Approvals</h1>
      <p className="mb-6 text-sm text-slate-500">Review and manage recruiter account status.</p>

      <ErrorBanner message={error} />

      <div className="mb-6 flex gap-2">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`rounded-lg px-4 py-2 text-sm font-medium capitalize transition ${
              tab === t ? 'bg-brand-600 text-white' : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : recruiters.length === 0 ? (
        <EmptyState message={`No ${tab} recruiters.`} />
      ) : (
        <div className="space-y-3">
          {recruiters.map((r) => (
            <div key={r.recruiter_id} className="card flex items-center justify-between">
              <div>
                <p className="font-medium text-slate-800">{r.full_name}</p>
                <p className="text-sm text-slate-500">{r.company_name} · {r.email}</p>
              </div>
              <div className="flex gap-2">
                {tab === 'pending' && (
                  <>
                    <button disabled={actingOn === r.recruiter_id} onClick={() => handleAction('approve', r.recruiter_id)} className="btn-primary text-xs">
                      Approve
                    </button>
                    <button disabled={actingOn === r.recruiter_id} onClick={() => handleAction('reject', r.recruiter_id)} className="btn-secondary text-xs border-rose-300 text-rose-600">
                      Reject
                    </button>
                  </>
                )}
                {tab === 'approved' && (
                  <button disabled={actingOn === r.recruiter_id} onClick={() => handleAction('suspend', r.recruiter_id)} className="btn-secondary text-xs border-amber-300 text-amber-600">
                    Suspend
                  </button>
                )}
                {(tab === 'suspended' || tab === 'rejected') && (
                  <button disabled={actingOn === r.recruiter_id} onClick={() => handleAction('activate', r.recruiter_id)} className="btn-primary text-xs">
                    Activate
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </DashboardLayout>
  )
}
