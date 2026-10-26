import type { ReactNode } from 'react'
import { Navigate, Outlet, useLocation, useSearchParams } from 'react-router'
import { AccessDenied, PageLoader } from '@/components/ui/States'
import { safeNextPath } from '@/lib/navigation'
import { useAuth } from './AuthContext'

/**
 * UX-only route guards. They decide what to render; the backend still
 * authorizes every request independently.
 */
export function RequireAuth({ children }: { children?: ReactNode }) {
  const { status } = useAuth()
  const location = useLocation()
  if (status === 'loading') return <PageLoader />
  if (status === 'anonymous') {
    return <Navigate to={`/login?next=${encodeURIComponent(location.pathname + location.search)}`} replace />
  }
  return children ?? <Outlet />
}

export function RequireAdmin({ children }: { children?: ReactNode }) {
  const { isAdmin } = useAuth()
  return <RequireAuth>{isAdmin ? (children ?? <Outlet />) : <AccessDenied message="The admin console is available to admin and superadmin accounts only." />}</RequireAuth>
}

/** For login/register pages: signed-in users are sent on to `?next=` (or home). */
export function RedirectIfAuthenticated({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  const [params] = useSearchParams()
  if (status === 'loading') return <PageLoader />
  if (status === 'authenticated') return <Navigate to={safeNextPath(params.get('next'))} replace />
  return children
}
