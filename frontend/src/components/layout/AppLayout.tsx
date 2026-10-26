import { Outlet } from 'react-router'
import { APP_NAME } from '@/lib/env'
import { Header } from './Header'
import { ScrollToTop } from './ScrollToTop'

export function AppLayout() {
  return (
    <div className="flex min-h-dvh flex-col">
      <a href="#main" className="sr-only z-50 rounded-lg bg-white px-3 py-2 focus:not-sr-only focus:fixed focus:top-3 focus:left-3">
        Skip to content
      </a>
      <ScrollToTop />
      <Header />
      <main id="main" className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
        <Outlet />
      </main>
      <footer className="border-t border-stone-200/80">
        <div className="mx-auto flex max-w-7xl flex-col gap-2 px-4 py-6 text-sm text-stone-500 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
          <p>© {new Date().getFullYear()} {APP_NAME}. Every bid is binding once the seller accepts.</p>
          <p>Auctions run for one hour after approval.</p>
        </div>
      </footer>
    </div>
  )
}
