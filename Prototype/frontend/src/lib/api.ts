export type ModelName = 'yolo' | 'ssd' | 'fasterrcnn'

export type DetectionItem = {
  label: string
  score: number
  box: { x1: number; y1: number; x2: number; y2: number }
}

export type DetectResponse = {
  model: string
  device: string
  processing_ms: number
  detections: DetectionItem[]
  asset_id?: number
  run_id?: number
}

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

export function apiUrl(path: string) {
  return `${API_BASE}${path}`
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('ann_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function register(email: string, password: string): Promise<{ access_token: string; refresh_token?: string }> {
  const res = await fetch(apiUrl('/auth/register'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) throw new Error(`Failed /auth/register: ${res.status}`)
  return await res.json()
}

export async function login(email: string, password: string): Promise<{ access_token: string; refresh_token?: string }> {
  const fd = new URLSearchParams()
  fd.set('username', email)
  fd.set('password', password)
  const res = await fetch(apiUrl('/auth/login'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: fd,
  })
  if (!res.ok) throw new Error(`Failed /auth/login: ${res.status}`)
  return await res.json()
}

export async function refreshToken(refresh_token: string): Promise<{ access_token: string; refresh_token?: string }> {
  const res = await fetch(apiUrl('/auth/refresh'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token }),
  })
  if (!res.ok) throw new Error(`Failed /auth/refresh: ${res.status}`)
  return await res.json()
}

export async function logout(refresh_token: string): Promise<void> {
  await fetch(apiUrl('/auth/logout'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token }),
  })
}

export async function fetchModels(): Promise<Record<string, string>> {
  const res = await fetch(apiUrl('/models'), { headers: authHeaders() })
  if (!res.ok) throw new Error(`Failed /models: ${res.status}`)
  const json = await res.json()
  return json.supported
}

export async function detectImage(params: {
  file: File
  model: ModelName
  scoreThresh: number
}): Promise<DetectResponse> {
  const fd = new FormData()
  fd.append('file', params.file)
  const url = new URL(apiUrl('/detect/image'))
  url.searchParams.set('model', params.model)
  url.searchParams.set('score_thresh', String(params.scoreThresh))
  const res = await fetch(url, { method: 'POST', body: fd, headers: authHeaders() })
  if (!res.ok) throw new Error(`Failed /detect/image: ${res.status}`)
  return await res.json()
}

export async function detectVideo(params: {
  file: File
  model: ModelName
  scoreThresh: number
  maxFrames: number
}): Promise<any> {
  const fd = new FormData()
  fd.append('file', params.file)
  const url = new URL(apiUrl('/detect/video'))
  url.searchParams.set('model', params.model)
  url.searchParams.set('score_thresh', String(params.scoreThresh))
  url.searchParams.set('max_frames', String(params.maxFrames))
  const res = await fetch(url, { method: 'POST', body: fd, headers: authHeaders() })
  if (!res.ok) throw new Error(`Failed /detect/video: ${res.status}`)
  return await res.json()
}

export async function fetchCompare(): Promise<any> {
  const res = await fetch(apiUrl('/models/compare'), { headers: authHeaders() })
  if (!res.ok) throw new Error(`Failed /models/compare: ${res.status}`)
  return await res.json()
}

export async function fetchRecentRuns(): Promise<any> {
  const res = await fetch(apiUrl('/metrics/recent'), { headers: authHeaders() })
  if (!res.ok) throw new Error(`Failed /metrics/recent: ${res.status}`)
  return await res.json()
}

export async function fetchMe(): Promise<{ id: number; email: string; role: string }> {
  const res = await fetch(apiUrl('/auth/me'), { headers: authHeaders() })
  if (!res.ok) throw new Error(`Failed /auth/me: ${res.status}`)
  return await res.json()
}

export async function fetchJob(jobId: number): Promise<any> {
  const res = await fetch(apiUrl(`/jobs/${jobId}`), { headers: authHeaders() })
  if (!res.ok) throw new Error(`Failed /jobs/${jobId}: ${res.status}`)
  return await res.json()
}

export function downloadRunUrl(runId: number) {
  // token-protected download; use fetch+blob in UI
  return apiUrl(`/runs/${runId}/download`)
}

