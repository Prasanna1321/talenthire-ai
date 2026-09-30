// Belongs in: frontend/src/components/Navbar.jsx
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6">
      <div className="flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-sm font-bold text-white">
          TH
        </div>
        <span className="text-lg font-semibold text-slate-800">TalentHire AI</span>
      </div>

      {user && (
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm font-medium text-slate-800">{user.full_name}</p>
            <p className="text-xs capitalize text-slate-500">{user.role}</p>
          </div>
          <button onClick={handleLogout} className="btn-secondary text-xs">
            Log out
          </button>
        </div>
      )}
    </header>
  )
}
