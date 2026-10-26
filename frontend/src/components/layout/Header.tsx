import { ChevronDown, LogOut, Menu, Plus, ShieldCheck, User as UserIcon, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router'
import { toast } from 'sonner'
import { useAuth } from '@/auth/AuthContext'
import { buttonClasses } from '@/components/ui/buttonStyles'
import { cn } from '@/lib/cn'
import { Logo } from './Logo'

function useNavItems() {
  const { status, isAdmin } = useAuth()
  const items = [{ to: '/', label: 'Marketplace', end: true }]
  if (status === 'authenticated') items.push({ to: '/my-listings', label: 'My listings', end: false })
  if (isAdmin) items.push({ to: '/admin', label: 'Admin', end: false })
  return items
}

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    'rounded-lg px-3 py-2 text-sm font-medium transition-colors',
    isActive ? 'bg-stone-100 text-stone-900' : 'text-stone-600 hover:bg-stone-100/70 hover:text-stone-900',
  )

function RoleBadge({ role }: { role: string }) {
  if (role === 'user') return null
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-semibold tracking-wide text-brand-800 uppercase ring-1 ring-brand-200 ring-inset">
      <ShieldCheck className="size-3" aria-hidden />
      {role}
    </span>
  )
}

function UserMenu() {
  const { username, role, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onPointer = (e: PointerEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false)
    document.addEventListener('pointerdown', onPointer)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('pointerdown', onPointer)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  const signOut = async () => {
    setOpen(false)
    await logout()
    toast.success('Signed out')
    navigate('/')
  }

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-haspopup="menu"
        className="flex items-center gap-2 rounded-full py-1 pr-2 pl-1 text-sm font-medium text-stone-700 ring-1 ring-stone-200 hover:bg-stone-100"
      >
        <span className="flex size-7 items-center justify-center rounded-full bg-stone-900 text-xs font-semibold text-white uppercase">
          {username?.[0] ?? '?'}
        </span>
        <span className="max-w-32 truncate">{username}</span>
        <ChevronDown className="size-4 text-stone-400" aria-hidden />
      </button>
      {open && (
        <div role="menu" className="absolute right-0 z-40 mt-2 w-60 overflow-hidden rounded-xl bg-white py-1 shadow-lift ring-1 ring-stone-200">
          <div className="border-b border-stone-100 px-4 py-3">
            <p className="truncate text-sm font-medium text-stone-900">{username}</p>
            <div className="mt-1">{role && role !== 'user' ? <RoleBadge role={role} /> : <span className="text-xs text-stone-500">Member</span>}</div>
          </div>
          <Link role="menuitem" to="/account" onClick={() => setOpen(false)} className="flex items-center gap-2 px-4 py-2 text-sm text-stone-700 hover:bg-stone-50">
            <UserIcon className="size-4 text-stone-400" aria-hidden /> Account & security
          </Link>
          <button role="menuitem" type="button" onClick={signOut} className="flex w-full items-center gap-2 px-4 py-2 text-sm text-stone-700 hover:bg-stone-50">
            <LogOut className="size-4 text-stone-400" aria-hidden /> Sign out
          </button>
        </div>
      )}
    </div>
  )
}

export function Header() {
  const { status, username, role, logout } = useAuth()
  const items = useNavItems()
  const location = useLocation()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)

  // Close the mobile menu on navigation.
  const [lastPath, setLastPath] = useState(location.pathname)
  if (lastPath !== location.pathname) {
    setLastPath(location.pathname)
    setMobileOpen(false)
  }

  const loginHref = `/login?next=${encodeURIComponent(location.pathname + location.search)}`

  return (
    <header className="sticky top-0 z-30 border-b border-stone-200/80 bg-white/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-4 px-4 sm:px-6 lg:px-8">
        <Logo />
        <nav aria-label="Main" className="ml-4 hidden items-center gap-1 md:flex">
          {items.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={navLinkClass}>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="ml-auto hidden items-center gap-2 md:flex">
          {status === 'authenticated' ? (
            <>
              <Link to="/sell" className={buttonClasses({ variant: 'brand', size: 'sm' })}>
                <Plus className="size-4" aria-hidden /> New listing
              </Link>
              <UserMenu />
            </>
          ) : status === 'anonymous' ? (
            <>
              <Link to={loginHref} className={buttonClasses({ variant: 'ghost', size: 'sm' })}>
                Sign in
              </Link>
              <Link to="/register" className={buttonClasses({ variant: 'primary', size: 'sm' })}>
                Create account
              </Link>
            </>
          ) : (
            <div className="h-8 w-40 animate-pulse rounded-full bg-stone-100" aria-hidden />
          )}
        </div>

        <button
          type="button"
          className="ml-auto inline-flex size-10 items-center justify-center rounded-lg text-stone-700 hover:bg-stone-100 md:hidden"
          aria-expanded={mobileOpen}
          aria-controls="mobile-nav"
          aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
          onClick={() => setMobileOpen((v) => !v)}
        >
          {mobileOpen ? <X className="size-5" /> : <Menu className="size-5" />}
        </button>
      </div>

      {mobileOpen && (
        <div id="mobile-nav" className="border-t border-stone-200 bg-white px-4 pt-2 pb-4 md:hidden">
          {status === 'authenticated' && (
            <div className="flex items-center gap-3 border-b border-stone-100 px-1 py-3">
              <span className="flex size-9 items-center justify-center rounded-full bg-stone-900 text-sm font-semibold text-white uppercase">
                {username?.[0] ?? '?'}
              </span>
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{username}</p>
                {role && <RoleBadge role={role} />}
              </div>
            </div>
          )}
          <nav aria-label="Mobile" className="mt-2 flex flex-col gap-1">
            {items.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.end} className={navLinkClass}>
                {item.label}
              </NavLink>
            ))}
            {status === 'authenticated' && (
              <NavLink to="/account" className={navLinkClass}>
                Account & security
              </NavLink>
            )}
          </nav>
          <div className="mt-3 grid gap-2">
            {status === 'authenticated' ? (
              <>
                <Link to="/sell" className={buttonClasses({ variant: 'brand' })}>
                  <Plus className="size-4" aria-hidden /> New listing
                </Link>
                <button
                  type="button"
                  className={buttonClasses({ variant: 'secondary' })}
                  onClick={async () => {
                    await logout()
                    toast.success('Signed out')
                    navigate('/')
                  }}
                >
                  <LogOut className="size-4" aria-hidden /> Sign out
                </button>
              </>
            ) : (
              <>
                <Link to="/register" className={buttonClasses({ variant: 'primary' })}>
                  Create account
                </Link>
                <Link to={loginHref} className={buttonClasses({ variant: 'secondary' })}>
                  Sign in
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  )
}
