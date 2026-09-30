// Belongs in: frontend/src/api/interviewsApi.js
import apiClient from './axiosClient'

export const generateQuestions = (payload) => apiClient.post('/interviews/questions/generate', payload)
export const listQuestionsForJob = (jobId) => apiClient.get(`/interviews/questions/job/${jobId}`)

export const startSession = (payload) => apiClient.post('/interviews/sessions/start', payload)
export const mySessions = () => apiClient.get('/interviews/sessions/mine')
export const getReport = (sessionId) => apiClient.get(`/interviews/sessions/${sessionId}/report`)
// PHASE 7: PDF report download — response is binary, so blob type is required
export const downloadReportPdf = (sessionId) =>
  apiClient.get(`/interviews/sessions/${sessionId}/report/pdf`, { responseType: 'blob' })
export const completeSession = (sessionId, payload) =>
  apiClient.post(`/interviews/sessions/${sessionId}/complete`, payload)

export const submitTextAnswer = (sessionId, payload) =>
  apiClient.post(`/interviews/sessions/${sessionId}/answer/text`, payload)

export const submitAudioAnswer = (sessionId, questionId, audioBlob) => {
  const formData = new FormData()
  formData.append('audio_file', audioBlob, 'answer.webm')
  return apiClient.post(
    `/interviews/sessions/${sessionId}/answer/audio?question_id=${questionId}`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
}
