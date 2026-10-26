import type { Token } from './types'

/**
 * The backend issues bearer tokens in the response body (no cookies), so the
 * frontend has to hold them. The short-lived access token lives only in memory;
 * the refresh token is persisted so a reload can restore the session. The backend
 * rotates refresh tokens on every use and revokes them on logout/password change.
 */
const REFRESH_KEY = 'lotwise.refreshToken'

let accessToken: string | null = null
const listeners = new Set<() => void>()

function readStorage() {
  try {
    return localStorage.getItem(REFRESH_KEY)
  } catch {
    return null
  }
}

function writeStorage(value: string | null) {
  try {
    if (value) localStorage.setItem(REFRESH_KEY, value)
    else localStorage.removeItem(REFRESH_KEY)
  } catch {
    // Storage unavailable (private mode, blocked): session lasts for this page only.
  }
}

let refreshToken: string | null = readStorage()

export const tokenStore = {
  getAccessToken: () => accessToken,
  getRefreshToken: () => refreshToken,
  setTokens(tokens: Pick<Token, 'access_token' | 'refresh_token'>) {
    accessToken = tokens.access_token
    refreshToken = tokens.refresh_token
    writeStorage(refreshToken)
    listeners.forEach((fn) => fn())
  },
  clear() {
    const hadTokens = accessToken !== null || refreshToken !== null
    accessToken = null
    refreshToken = null
    writeStorage(null)
    if (hadTokens) listeners.forEach((fn) => fn())
  },
  subscribe(fn: () => void) {
    listeners.add(fn)
    return () => {
      listeners.delete(fn)
    }
  },
}

/** Reads the unverified JWT payload. Used only for display (username); the backend verifies tokens. */
export function decodeJwt(token: string): { sub?: string; exp?: number } | null {
  try {
    const payload = token.split('.')[1]
    const json = atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
    return JSON.parse(json)
  } catch {
    return null
  }
}
