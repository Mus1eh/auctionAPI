import { createContext, useContext } from 'react'
import type { Role } from '@/api/types'

export type AuthStatus = 'loading' | 'authenticated' | 'anonymous'

export interface AuthContextValue {
  status: AuthStatus
  username: string | null
  role: Role | null
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
