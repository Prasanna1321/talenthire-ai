// Belongs in: frontend/src/api/jobsApi.js
import apiClient from './axiosClient'

// Jobs
export const listJobs = (params = {}) => apiClient.get('/jobs', { params })
export const getJob = (jobId) => apiClient.get(`/jobs/${jobId}`)
export const createJob = (payload) => apiClient.post('/jobs', payload)
export const updateJob = (jobId, payload) => apiClient.put(`/jobs/${jobId}`, payload)
export const deleteJob = (jobId) => apiClient.delete(`/jobs/${jobId}`)
export const listMyJobs = () => apiClient.get('/jobs/recruiter/mine')

// Applications
export const applyToJob = (payload) => apiClient.post('/applications', payload)
export const myApplications = () => apiClient.get('/applications/candidate/mine')
export const jobApplicants = (jobId) => apiClient.get(`/applications/job/${jobId}`)
// PHASE 8: ATS score + aptitude score + interview score + matched/missing skills all in one place
export const jobCandidatesDetailed = (jobId) => apiClient.get(`/applications/job/${jobId}/candidates`)
export const updateApplicationStatus = (applicationId, status) =>
  apiClient.put(`/applications/${applicationId}/status`, { status })
