// Belongs in: frontend/src/api/resumesApi.js
import apiClient from './axiosClient'

export const uploadResume = (file, force = false) => {
  const formData = new FormData()
  formData.append('file', file)
  return apiClient.post('/resumes/upload', formData, {
    params: { force },
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const listMyResumes = () => apiClient.get('/resumes/mine')
export const resumeHistory = () => apiClient.get('/resumes/history')
export const getResume = (resumeId) => apiClient.get(`/resumes/${resumeId}`)
export const getJobRecommendations = () => apiClient.get('/resumes/recommendations/jobs')
