import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import type { ReactElement } from 'react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router'
import { vi } from 'vitest'
import { AuthProvider } from '@/auth/AuthProvider'

export function jsonResponse(body: unknown, status = 200) {
  return new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

/** Builds a JWT-shaped token with the given subject (signature is irrelevant to the client). */
export function fakeJwt(sub: string) {
  const b64 = (o: object) => btoa(JSON.stringify(o)).replace(/=+$/, '')
  return `${b64({ alg: 'HS256', typ: 'JWT' })}.${b64({ sub, exp: 9999999999 })}.sig`
}

type Handler = (url: URL, init: RequestInit) => Response | Promise<Response>

/** Routes fetch calls by "METHOD /path" (path without the /api prefix). Unmatched calls fail the test. */
export function mockFetch(routes: Record<string, Handler | Response | object>) {
  const fn = vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
    const url = new URL(String(input), 'http://localhost')
    const key = `${init.method ?? 'GET'} ${url.pathname.replace(/^\/api/, '')}`
    if (!(key in routes)) throw new Error(`Unexpected request: ${key}`)
    const route = routes[key]
    if (typeof route === 'function') return (route as Handler)(url, init)
    if (route instanceof Response) return route.clone()
    return jsonResponse(route)
  })
  vi.stubGlobal('fetch', fn)
  return fn
}

function LocationProbe() {
  const location = useLocation()
  return <div data-testid="location">{location.pathname + location.search}</div>
}

export function renderApp(ui: ReactElement, { route = '/', path = '/' }: { route?: string; path?: string } = {}) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>
        <AuthProvider>
          <Routes>
            <Route path={path} element={ui} />
            <Route path="*" element={<div>other page</div>} />
          </Routes>
          <LocationProbe />
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}
