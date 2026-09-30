// Belongs in: frontend/src/pages/admin/UserManagement.jsx
import { useEffect, useState } from 'react'
import DashboardLayout from '../../components/DashboardLayout.jsx'
import { ErrorBanner, LoadingSpinner } from '../../components/Misc.jsx'
import { listAllUsers, setUserActiveStatus } from '../../api/dashboardApi.js'

export default function UserManagement() {
  const [users, setUsers] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const loadUsers = () => {
    setLoading(true)
    listAllUsers()
      .then((res) => setUsers(res.data))
      .catch(() => setError('Could not load users.'))
      .finally(() => setLoading(false))
  }

  useEffect(loadUsers, [])

  const toggleStatus = async (user) => {
    try {
      await setUserActiveStatus(user.user_id, !user.is_active)
      setUsers((prev) =>
        prev.map((u) => (u.user_id === user.user_id ? { ...u, is_active: !u.is_active } : u)),
      )
    } catch {
      setError('Could not update user status.')
    }
  }

  return (
    <DashboardLayout role="admin">
      <h1 className="mb-1 text-2xl font-bold text-slate-900">Manage Users</h1>
      <p className="mb-6 text-sm text-slate-500">Activate or deactivate candidate, recruiter, and admin accounts.</p>

      <ErrorBanner message={error} />
      {loading ? (
        <LoadingSpinner />
      ) : (
        <div className="card overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Role</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.user_id} className="border-t border-slate-100">
                  <td className="px-4 py-3 font-medium text-slate-800">{u.full_name}</td>
                  <td className="px-4 py-3 text-slate-500">{u.email}</td>
                  <td className="px-4 py-3 capitalize text-slate-500">{u.role}</td>
                  <td className="px-4 py-3">
                    <span className={`badge ${u.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                      {u.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button onClick={() => toggleStatus(u)} className="btn-secondary text-xs">
                      {u.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </DashboardLayout>
  )
}
