// Belongs in: frontend/src/context/AuthContext.jsx
// Provides the current user + auth actions (login, register, verifyOtp,
// logout) to the whole app via React Context, backed by localStorage.
//
// PHASE 2 CHANGE: register() no longer returns a logged-in session — the
// backend now requires email verification first. register() just tells
// the caller "OTP sent"; the caller (Register.jsx) redirects to the OTP
// verification page, which calls verifyOtp() to actually get tokens.

import { createContext, useContext, useEffect, useState } from 'react'
import { loginUser, registerUser, verifyOtpRequest } from '../api/authApi'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const storedUser = localStorage.getItem('user')
    const token = localStorage.getItem('access_token')
    if (storedUser && token) {
      setUser(JSON.parse(storedUser))
    }
    setLoading(false)
  }, [])

  const persistSession = (data) => {
    const userInfo = { user_id: data.user_id, full_name: data.full_name, role: data.role }
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('user', JSON.stringify(userInfo))
    setUser(userInfo)
    return userInfo
  }

  const login = async (email, password) => {
    const { data } = await loginUser({ email, password })
    return persistSession(data)
  }

  const register = async (payload) => {
    // PHASE 2: returns {detail: "..."} only — no session yet.
    const { data } = await registerUser(payload)
    return data
  }

  const verifyOtp = async (email, otp, purpose) => {
    const { data } = await verifyOtpRequest({ email, otp, purpose })
    return persistSession(data)
  }

  const logout = () => {
    localStorage.clear()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, verifyOtp, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
