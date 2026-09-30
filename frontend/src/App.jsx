// Belongs in: frontend/src/App.jsx
// PHASE 1 CHANGE: "/" is now the public HomePage (no auth required, no
// auto-redirect to /login). Authenticated users can still reach their
// dashboard via the Navbar's "Dashboard" link, or by visiting their
// dashboard URL directly (ProtectedRoute still guards those as before).
// Everything else (candidate/recruiter/admin routes) is UNCHANGED.

import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from './routes/ProtectedRoute.jsx'

import HomePage from './pages/public/HomePage.jsx'
import Login from './pages/auth/Login.jsx'
import Register from './pages/auth/Register.jsx'
import VerifyOtp from './pages/auth/VerifyOtp.jsx'
import ForgotPassword from './pages/auth/ForgotPassword.jsx'

import CandidateDashboard from './pages/candidate/CandidateDashboard.jsx'
import ResumeUpload from './pages/candidate/ResumeUpload.jsx'
import JobBrowse from './pages/candidate/JobBrowse.jsx'
import MockInterview from './pages/candidate/MockInterview.jsx'
import InterviewReports from './pages/candidate/InterviewReports.jsx'
import AptitudeTest from './pages/candidate/AptitudeTest.jsx'
import VoiceInterview from './pages/candidate/VoiceInterview.jsx'

import RecruiterDashboard from './pages/recruiter/RecruiterDashboard.jsx'
import JobManagement from './pages/recruiter/JobManagement.jsx'
import RecruiterAnalytics from './pages/recruiter/RecruiterAnalytics.jsx'

import AdminDashboard from './pages/admin/AdminDashboard.jsx'
import UserManagement from './pages/admin/UserManagement.jsx'
import RecruiterApprovals from './pages/admin/RecruiterApprovals.jsx'

export default function App() {
  return (
    <Routes>
      {/* Public marketing/landing page — no login required */}
      <Route path="/" element={<HomePage />} />

      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/verify-otp" element={<VerifyOtp />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />

      {/* Candidate routes */}
      <Route path="/candidate/dashboard" element={<ProtectedRoute allowedRoles={['candidate']}><CandidateDashboard /></ProtectedRoute>} />
      <Route path="/candidate/resume" element={<ProtectedRoute allowedRoles={['candidate']}><ResumeUpload /></ProtectedRoute>} />
      <Route path="/candidate/jobs" element={<ProtectedRoute allowedRoles={['candidate']}><JobBrowse /></ProtectedRoute>} />
      <Route path="/candidate/interview" element={<ProtectedRoute allowedRoles={['candidate']}><MockInterview /></ProtectedRoute>} />
      <Route path="/candidate/reports" element={<ProtectedRoute allowedRoles={['candidate']}><InterviewReports /></ProtectedRoute>} />
      <Route path="/candidate/aptitude-test" element={<ProtectedRoute allowedRoles={['candidate']}><AptitudeTest /></ProtectedRoute>} />
      <Route path="/candidate/voice-interview" element={<ProtectedRoute allowedRoles={['candidate']}><VoiceInterview /></ProtectedRoute>} />

      {/* Recruiter routes */}
      <Route path="/recruiter/dashboard" element={<ProtectedRoute allowedRoles={['recruiter']}><RecruiterDashboard /></ProtectedRoute>} />
      <Route path="/recruiter/jobs" element={<ProtectedRoute allowedRoles={['recruiter']}><JobManagement /></ProtectedRoute>} />
      <Route path="/recruiter/analytics" element={<ProtectedRoute allowedRoles={['recruiter']}><RecruiterAnalytics /></ProtectedRoute>} />

      {/* Admin routes */}
      <Route path="/admin/dashboard" element={<ProtectedRoute allowedRoles={['admin']}><AdminDashboard /></ProtectedRoute>} />
      <Route path="/admin/users" element={<ProtectedRoute allowedRoles={['admin']}><UserManagement /></ProtectedRoute>} />
      <Route path="/admin/recruiters" element={<ProtectedRoute allowedRoles={['admin']}><RecruiterApprovals /></ProtectedRoute>} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}