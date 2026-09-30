// Belongs in: frontend/src/components/Sidebar.jsx
import { NavLink } from 'react-router-dom'

const NAV_LINKS = {
  candidate: [
    { to: '/candidate/dashboard', label: 'Dashboard' },
    { to: '/candidate/resume', label: 'Resume Upload' },
    { to: '/candidate/jobs', label: 'Browse Jobs' },

    // Phase 5: Aptitude test before live AI interview
    { to: '/candidate/aptitude-test', label: 'Aptitude Test' },

    // Main interview experience
    { to: '/candidate/voice-interview', label: 'Live AI Interview' },

    { to: '/candidate/reports', label: 'Interview Reports' },
  ],

  recruiter: [
    { to: '/recruiter/dashboard', label: 'Dashboard' },
    { to: '/recruiter/jobs', label: 'Manage Jobs' },
    { to: '/recruiter/analytics', label: 'Analytics' },
  ],

  admin: [
    { to: '/admin/dashboard', label: 'Dashboard' },
    { to: '/admin/users', label: 'Manage Users' },
    { to: '/admin/recruiters', label: 'Recruiter Approvals' },
  ],
}

export default function Sidebar({ role }) {
  const links = NAV_LINKS[role] || []

  return (
    <aside className="w-60 shrink-0 border-r border-slate-200 bg-white p-4">
      <nav className="flex flex-col gap-1">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              `rounded-lg px-3 py-2 text-sm font-medium transition ${
                isActive
                  ? 'bg-brand-50 text-brand-700'
                  : 'text-slate-600 hover:bg-slate-100'
              }`
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}