import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

export async function startSession(data = {}) {
  const res = await api.post('/session/start', data)
  return res.data
}

export async function sendMessage(sessionId, message) {
  const res = await api.post('/inquiry/message', { session_id: sessionId, message })
  return res.data
}

export async function sendMessageStream(sessionId, message) {
  const response = await fetch('/api/inquiry/message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  })
  return response.body
}

export async function analyzeSession(sessionId) {
  const res = await api.post('/inquiry/analyze', { session_id: sessionId })
  return res.data
}

export async function checkSafety(message) {
  const res = await api.post('/safety/check', { session_id: 'check', message })
  return res.data
}

export async function getHealthRecords(limit = 20, offset = 0) {
  const res = await api.get('/health/records', { params: { limit, offset } })
  return res.data
}

export async function createHealthRecord(sessionId, notes = '') {
  const res = await api.post('/health/record', { session_id: sessionId, notes })
  return res.data
}
