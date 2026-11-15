import { createContext, useContext } from 'react'

export type AuthStatus = 'loading' | 'authenticated' | 'anonymous'

export interface AuthContextValue {
  status: AuthStatus
  username: string | null
  roles: string[]
  /** The most powerful role held, for display. */
  primaryRole: 'user' | 'admin' | 'superadmin' | null
  permissions: string[]
  /** UX only: whether the signed-in user holds a permission. The API enforces it regardless. */
  can: (permission: string) => boolean
  isAdmin: boolean
  isSuperadmin: boolean
  login: (identifier: string, password: string) => Promise<void>
  /** Revokes the refresh token on the server and clears local state. */
  logout: () => Promise<void>
  /** Clears local state only; for when the server already revoked the session. */
  endSession: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must be used inside <AuthProvider>')
  return value
}
