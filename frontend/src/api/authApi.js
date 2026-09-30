// Belongs in: frontend/src/api/authApi.js
import apiClient from './axiosClient'

export const registerUser = (payload) => apiClient.post('/auth/register', payload)
export const loginUser = (payload) => apiClient.post('/auth/login', payload)
export const refreshToken = (refresh_token) => apiClient.post('/auth/refresh', { refresh_token })
export const getMe = () => apiClient.get('/users/me')

// PHASE 2: OTP verification + forgot/reset password
export const sendOtpRequest = (payload) => apiClient.post('/auth/send-otp', payload)
export const verifyOtpRequest = (payload) => apiClient.post('/auth/verify-otp', payload)
export const forgotPasswordRequest = (payload) => apiClient.post('/auth/forgot-password', payload)
export const resetPasswordRequest = (payload) => apiClient.post('/auth/reset-password', payload)
