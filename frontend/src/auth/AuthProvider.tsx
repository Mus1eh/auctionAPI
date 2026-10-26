import { useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { authApi } from '@/api/endpoints'
import { PRIVATE_QUERY_ROOTS } from '@/api/queries'
import { tokenStore } from '@/api/tokens'
import type { Role } from '@/api/types'
import { AuthContext, type AuthContextValue, type AuthStatus } from './AuthContext'
import { loadSessionInfo, restoreSession } from './session'

interface State {
  status: AuthStatus
  username: string | null
  role: Role | null
}

const ANONYMOUS: State = { status: 'anonymous', username: null, role: null }

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [state, setState] = useState<State>(() =>
    tokenStore.getRefreshToken() ? { status: 'loading', username: null, role: null } : ANONYMOUS,
  )

  const dropPrivateData = useCallback(() => {
    queryClient.removeQueries({ predicate: (q) => PRIVATE_QUERY_ROOTS.includes(String(q.queryKey[0])) })
  }, [queryClient])

  useEffect(() => {
    if (state.status !== 'loading') return
    let cancelled = false
    restoreSession().then((info) => {
      if (cancelled) return
      setState(info ? { status: 'authenticated', ...info } : ANONYMOUS)
    })
    return () => {
      cancelled = true
    }
  }, [state.status])

  // A failed refresh mid-session clears the tokens; reflect that in the UI.
  useEffect(
    () =>
      tokenStore.subscribe(() => {
        if (!tokenStore.getRefreshToken()) {
          setState((prev) => (prev.status === 'authenticated' ? ANONYMOUS : prev))
          dropPrivateData()
        }
      }),
    [dropPrivateData],
  )

  const login = useCallback(async (identifier: string, password: string) => {
    const tokens = await authApi.login(identifier, password)
    tokenStore.setTokens(tokens)
    const info = await loadSessionInfo()
    setState({ status: 'authenticated', ...info })
  }, [])

  const endSession = useCallback(() => {
    tokenStore.clear()
    setState(ANONYMOUS)
    dropPrivateData()
  }, [dropPrivateData])

  const logout = useCallback(async () => {
    const refreshToken = tokenStore.getRefreshToken()
    endSession()
    if (refreshToken) {
      try {
        await authApi.logout(refreshToken)
      } catch {
        // Local session is already gone; the token expires server-side regardless.
      }
    }
  }, [endSession])

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      isAdmin: state.role === 'admin' || state.role === 'superadmin',
      isSuperadmin: state.role === 'superadmin',
      login,
      logout,
      endSession,
    }),
    [state, login, logout, endSession],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
