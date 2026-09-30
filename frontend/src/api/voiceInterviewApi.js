// Belongs in: frontend/src/api/voiceInterviewApi.js
// Phase 6: requests a short-lived Gemini Live API ephemeral token from OUR
// backend (which holds the real GEMINI_API_KEY server-side) — the frontend
// never sees the real key, only this single-use ephemeral token.
import apiClient from './axiosClient'

export const getVoiceSessionToken = (jobId) =>
  apiClient.post('/interview/voice/session-token', null, { params: jobId ? { job_id: jobId } : {} })
