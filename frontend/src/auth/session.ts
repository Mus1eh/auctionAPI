import { isApiError, refreshSession } from '@/api/client'
import { adminApi } from '@/api/endpoints'
import { decodeJwt, tokenStore } from '@/api/tokens'
import type { Role } from '@/api/types'

export interface SessionInfo {
  username: string
  role: Role
}

/**
 * The API has no "current user" endpoint. The username comes from the JWT `sub`
 * claim and the role from probing /admin/dashboard (200 → admin/superadmin, 403 → user).
 */
export async function loadSessionInfo(): Promise<SessionInfo> {
  const token = tokenStore.getAccessToken()
  const username = (token && decodeJwt(token)?.sub) || ''
  try {
    const dashboard = await adminApi.dashboard()
    return { username: dashboard.username || username, role: dashboard.role }
  } catch (error) {
    if (isApiError(error, 401)) throw error
    // 403 is the expected answer for regular users. Any other failure falls back to the
    // least-privileged role; the backend still enforces permissions either way.
    return { username, role: 'user' }
  }
}

let restoring: Promise<SessionInfo | null> | null = null

/** Restores a session from the stored refresh token. Deduplicated for StrictMode double effects. */
export function restoreSession(): Promise<SessionInfo | null> {
  restoring ??= (async () => {
    if (!tokenStore.getRefreshToken()) return null
    if (!(await refreshSession())) return null
    return loadSessionInfo()
  })()
    .catch(() => null)
    .finally(() => {
      restoring = null
    })
  return restoring
}
