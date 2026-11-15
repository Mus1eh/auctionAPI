import { isApiError, refreshSession } from '@/api/client'
import { usersApi } from '@/api/endpoints'
import { decodeJwt, tokenStore } from '@/api/tokens'

export interface SessionInfo {
  username: string
  roles: string[]
  permissions: string[]
}

/** Who is signed in, the roles they hold and every permission those roles grant (GET /users/me). */
export async function loadSessionInfo(): Promise<SessionInfo> {
  const token = tokenStore.getAccessToken()
  const username = (token && decodeJwt(token)?.sub) || ''
  try {
    const me = await usersApi.me()
    return { username: me.username || username, roles: me.roles, permissions: me.permissions }
  } catch (error) {
    if (isApiError(error, 401)) throw error
    // Any other failure falls back to no permissions; the backend still enforces them either way.
    return { username, roles: [], permissions: [] }
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
