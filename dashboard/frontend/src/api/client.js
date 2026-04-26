const BASE = '/api'

async function get(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`)
  return res.json()
}

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`)
  return res.json()
}

export const api = {
  getPendingJobs: () => get('/pending'),
  getPendingEmails: () => get('/emails/pending'),
  getStats: () => get('/stats'),
  getHistory: () => get('/history'),
  getFailed: () => get('/failed'),
  decideJob: (id, decision) => post(`/decision/${id}`, { decision }),
  decideEmail: (id, decision) => post(`/email-decision/${id}`, { decision }),
}
