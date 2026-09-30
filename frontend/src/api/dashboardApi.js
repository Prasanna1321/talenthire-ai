// Belongs in: frontend/src/api/dashboardApi.js
import apiClient from './axiosClient'

// Dashboards
export const candidateDashboard = () => apiClient.get('/users/candidate/dashboard')
export const recruiterDashboard = () => apiClient.get('/users/recruiter/dashboard')
export const adminDashboard = () => apiClient.get('/admin/dashboard')

// Candidate profile
export const getCandidateProfile = () => apiClient.get('/users/candidate/profile')
export const updateCandidateProfile = (payload) => apiClient.put('/users/candidate/profile', payload)
export const getRecruiterProfile = () => apiClient.get('/users/recruiter/profile')

// Analytics
export const recruiterAnalytics = () => apiClient.get('/analytics/recruiter')

// Notifications
export const myNotifications = () => apiClient.get('/notifications/mine')
export const markNotificationRead = (id) => apiClient.put(`/notifications/${id}/read`)
export const markAllNotificationsRead = () => apiClient.put('/notifications/read-all')

// Admin
export const listAllUsers = () => apiClient.get('/admin/users')
export const setUserActiveStatus = (userId, isActive) =>
  apiClient.put(`/admin/users/${userId}/status`, null, { params: { is_active: isActive } })

// PHASE 3: recruiter approval workflow
export const listRecruiters = (status) => apiClient.get('/admin/recruiters', { params: status ? { status } : {} })
export const approveRecruiter = (recruiterId) => apiClient.post(`/admin/recruiters/${recruiterId}/approve`)
export const rejectRecruiter = (recruiterId) => apiClient.post(`/admin/recruiters/${recruiterId}/reject`)
export const suspendRecruiter = (recruiterId) => apiClient.post(`/admin/recruiters/${recruiterId}/suspend`)
export const activateRecruiter = (recruiterId) => apiClient.post(`/admin/recruiters/${recruiterId}/activate`)
