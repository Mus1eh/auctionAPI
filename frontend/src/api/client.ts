import { API_BASE_URL } from '@/lib/env'
import { tokenStore } from './tokens'
import type { Token } from './types'

export interface FieldError {
  field: string
  message: string
}

export class ApiError extends Error {
  readonly status: number
  readonly detail: unknown
  readonly fieldErrors: FieldError[]

  constructor(status: number, message: string, detail?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
    this.fieldErrors = extractFieldErrors(detail)
  }
}

interface ValidationIssue {
  loc?: (string | number)[]
  msg?: string
}

function extractFieldErrors(detail: unknown): FieldError[] {
  if (!Array.isArray(detail)) return []
  return (detail as ValidationIssue[])
    .filter((issue) => issue && typeof issue.msg === 'string')
    .map((issue) => ({
      field: String(issue.loc?.[issue.loc.length - 1] ?? ''),
      message: issue.msg!.replace(/^Value error, /, ''),
    }))
}

/** FastAPI's `detail` is a string, a 422 validation array, or (CSV import) an object with a message. */
export function messageFromDetail(detail: unknown, fallback: string) {
  if (typeof detail === 'string' && detail) return detail
  if (Array.isArray(detail)) {
    const errors = extractFieldErrors(detail)
    if (errors.length) return errors.map((e) => (e.field ? `${e.field}: ${e.message}` : e.message)).join('; ')
  }
  if (detail && typeof detail === 'object' && 'message' in detail && typeof detail.message === 'string') {
    return detail.message
  }
  return fallback
}

const STATUS_FALLBACKS: Record<number, string> = {
  401: 'Your session has expired. Please sign in again.',
  403: 'You do not have permission to do that.',
  404: 'Not found.',
  409: 'That action conflicts with the current state. Refresh and try again.',
  422: 'Some of the submitted data is invalid.',
}

export function buildUrl(path: string, query?: Record<string, string | number | undefined>) {
  const url = `${API_BASE_URL}${path}`
  if (!query) return url
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined) params.set(key, String(value))
  }
  const qs = params.toString()
  return qs ? `${url}?${qs}` : url
}

async function parseBody(response: Response): Promise<unknown> {
  if (response.status === 204) return undefined
  const type = response.headers.get('content-type') ?? ''
  if (type.includes('application/json')) {
    try {
      return await response.json()
    } catch {
      return undefined
    }
  }
  const text = await response.text()
  return text || undefined
}

let refreshInFlight: Promise<boolean> | null = null

/**
 * Exchanges the stored refresh token for a new pair. The backend revokes the old
 * refresh token on use, so concurrent callers must share one request.
 */
export function refreshSession(): Promise<boolean> {
  refreshInFlight ??= (async () => {
    const refreshToken = tokenStore.getRefreshToken()
    if (!refreshToken) return false
    try {
      const response = await fetch(buildUrl('/auth/refresh'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })
      if (!response.ok) {
        if (response.status < 500) tokenStore.clear()
        return false
      }
      tokenStore.setTokens((await response.json()) as Token)
      return true
    } catch {
      return false
    }
  })().finally(() => {
    refreshInFlight = null
  })
  return refreshInFlight
}

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  json?: unknown
  body?: FormData | URLSearchParams
  query?: Record<string, string | number | undefined>
  auth?: boolean
  signal?: AbortSignal
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', json, body, query, auth = false, signal } = options

  if (auth && !tokenStore.getAccessToken() && tokenStore.getRefreshToken()) {
    await refreshSession()
  }
  if (auth && !tokenStore.getAccessToken()) {
    throw new ApiError(401, 'Please sign in to continue.')
  }

  const send = () => {
    const headers: Record<string, string> = { Accept: 'application/json' }
    if (json !== undefined) headers['Content-Type'] = 'application/json'
    const token = tokenStore.getAccessToken()
    if (auth && token) headers.Authorization = `Bearer ${token}`
    return fetch(buildUrl(path, query), {
      method,
      headers,
      body: json !== undefined ? JSON.stringify(json) : body,
      signal,
    })
  }

  let response: Response
  try {
    response = await send()
    if (response.status === 401 && auth && (await refreshSession())) {
      response = await send()
    }
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new ApiError(0, 'Cannot reach the server. Check your connection and that the API is running.')
  }

  const data = await parseBody(response)

  if (!response.ok) {
    const detail = data && typeof data === 'object' && 'detail' in data ? data.detail : data
    if (response.status === 401 && auth) tokenStore.clear()
    const fallback = STATUS_FALLBACKS[response.status] ?? `Request failed (${response.status}).`
    throw new ApiError(response.status, messageFromDetail(detail, fallback), detail)
  }

  return data as T
}

export function isApiError(error: unknown, status?: number): error is ApiError {
  return error instanceof ApiError && (status === undefined || error.status === status)
}
