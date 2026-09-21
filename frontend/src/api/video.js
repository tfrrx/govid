const BASE = (import.meta.env.VITE_API_BASE ?? '').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, code = 'http_error', status = 0) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
  }
}

async function request(path, { method = 'GET', body, signal } = {}) {
  let response
  try {
    response = await fetch(`${BASE}${path}`, {
      method,
      signal,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch (error) {
    if (error?.name === 'AbortError') throw error
    throw new ApiError('无法连接后端服务，请确认服务已启动', 'offline', 0)
  }

  const raw = await response.text()
  let data = null
  if (raw) {
    try {
      data = JSON.parse(raw)
    } catch {
      data = null
    }
  }

  if (!response.ok) {
    throw new ApiError(
      data?.detail || `请求失败（HTTP ${response.status}）`,
      data?.code || 'http_error',
      response.status,
    )
  }

  return data
}

export const api = {
  health: (options) => request('/api/health', options),

  parse: (url, options) => request('/api/parse', { ...options, method: 'POST', body: { url } }),

  createTask: (payload, options) =>
    request('/api/tasks', { ...options, method: 'POST', body: payload }),

  getTask: (taskId, options) => request(`/api/tasks/${taskId}`, options),

  cancelTask: (taskId, options) =>
    request(`/api/tasks/${taskId}/cancel`, { ...options, method: 'POST' }),
}

export function taskFileUrl(taskId) {
  return `${BASE}/api/tasks/${taskId}/file`
}

export function thumbnailUrl(url) {
  if (!url) return ''
  return `${BASE}/api/proxy/thumbnail?url=${encodeURIComponent(url)}`
}
