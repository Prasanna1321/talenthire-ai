// Belongs in: frontend/src/api/aptitudeApi.js
import apiClient from './axiosClient'

export const startAptitudeTest = () => apiClient.post('/aptitude/start')
export const getAptitudeQuestions = (testId) => apiClient.get('/aptitude/questions', { params: { test_id: testId } })
export const submitAptitudeTest = (payload) => apiClient.post('/aptitude/submit', payload)
export const getAptitudeResult = (testId) => apiClient.get('/aptitude/result', { params: { test_id: testId } })
