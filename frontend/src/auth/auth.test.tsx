import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { tokenStore } from '@/api/tokens'
import { LoginPage } from '@/pages/auth/LoginPage'
import { fakeJwt, jsonResponse, mockFetch, renderApp } from '@/test/utils'
import { useAuth } from './AuthContext'
import { RedirectIfAuthenticated, RequireAdmin, RequireAuth } from './guards'

function WhoAmI() {
  const { status, username, role } = useAuth()
  return <p>{`${status}:${username ?? '-'}:${role ?? '-'}`}</p>
}

describe('route guards', () => {
  it('redirects anonymous users to login with a return path', async () => {
    mockFetch({})
    renderApp(<RequireAuth><p>secret</p></RequireAuth>, { route: '/sell?x=1', path: '/sell' })
    expect(screen.queryByText('secret')).not.toBeInTheDocument()
    expect(screen.getByTestId('location')).toHaveTextContent('/login?next=%2Fsell%3Fx%3D1')
  })

  it('restores a session from the stored refresh token', async () => {
    tokenStore.setTokens({ access_token: 'stale', refresh_token: 'r1' })
    mockFetch({
      'POST /auth/refresh': { access_token: fakeJwt('carol'), refresh_token: 'r2', token_type: 'bearer' },
      'GET /admin/dashboard': jsonResponse({ detail: 'You do not have permission to perform this action.' }, 403),
    })
    renderApp(<RequireAuth><WhoAmI /></RequireAuth>)
    expect(await screen.findByText('authenticated:carol:user')).toBeInTheDocument()
  })

  it('shows access denied to signed-in non-admins on admin routes', async () => {
    tokenStore.setTokens({ access_token: 'stale', refresh_token: 'r1' })
    mockFetch({
      'POST /auth/refresh': { access_token: fakeJwt('carol'), refresh_token: 'r2', token_type: 'bearer' },
      'GET /admin/dashboard': jsonResponse({ detail: 'Forbidden' }, 403),
    })
    renderApp(<RequireAdmin><p>admin console</p></RequireAdmin>)
    expect(await screen.findByText('Access denied')).toBeInTheDocument()
    expect(screen.queryByText('admin console')).not.toBeInTheDocument()
  })

  it('lets admins through, with the role from /admin/dashboard', async () => {
    tokenStore.setTokens({ access_token: 'stale', refresh_token: 'r1' })
    mockFetch({
      'POST /auth/refresh': { access_token: fakeJwt('root'), refresh_token: 'r2', token_type: 'bearer' },
      'GET /admin/dashboard': { message: 'Welcome', username: 'root', role: 'superadmin' },
    })
    renderApp(<RequireAdmin><WhoAmI /></RequireAdmin>)
    expect(await screen.findByText('authenticated:root:superadmin')).toBeInTheDocument()
  })

  it('treats a rejected refresh token as signed out', async () => {
    tokenStore.setTokens({ access_token: 'stale', refresh_token: 'revoked' })
    mockFetch({ 'POST /auth/refresh': jsonResponse({ detail: 'Invalid refresh token' }, 401) })
    renderApp(<RequireAuth><p>secret</p></RequireAuth>, { route: '/account', path: '/account' })
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent('/login?next=%2Faccount'))
    expect(tokenStore.getRefreshToken()).toBeNull()
  })
})

describe('LoginPage', () => {
  const renderLogin = (route = '/login') =>
    renderApp(<RedirectIfAuthenticated><LoginPage /></RedirectIfAuthenticated>, { route, path: '/login' })

  it('validates required fields before calling the API', async () => {
    const fetchMock = mockFetch({})
    renderLogin()
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(await screen.findByText('Enter your username or email')).toBeInTheDocument()
    expect(screen.getByText('Enter your password')).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('shows a clear message for invalid credentials', async () => {
    mockFetch({ 'POST /auth/': jsonResponse({ detail: 'Could not validate credentials' }, 401) })
    renderLogin()
    await userEvent.type(screen.getByLabelText('Username or email'), 'alice')
    await userEvent.type(screen.getByLabelText('Password'), 'wrong-password')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(await screen.findByText('Incorrect username, email or password.')).toBeInTheDocument()
    expect(tokenStore.getRefreshToken()).toBeNull()
  })

  it('signs in, stores the refresh token and redirects to ?next=', async () => {
    mockFetch({
      'POST /auth/': { access_token: fakeJwt('alice'), refresh_token: 'refresh-1', token_type: 'bearer' },
      'GET /admin/dashboard': jsonResponse({ detail: 'Forbidden' }, 403),
    })
    renderLogin('/login?next=%2Fproducts%2F4')
    await userEvent.type(screen.getByLabelText('Username or email'), 'alice')
    await userEvent.type(screen.getByLabelText('Password'), 'correct-horse')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent('/products/4'))
    expect(tokenStore.getRefreshToken()).toBe('refresh-1')
  })

  it('ignores off-site ?next= targets', async () => {
    mockFetch({
      'POST /auth/': { access_token: fakeJwt('alice'), refresh_token: 'refresh-1', token_type: 'bearer' },
      'GET /admin/dashboard': jsonResponse({}, 403),
    })
    renderLogin('/login?next=%2F%2Fevil.example')
    await userEvent.type(screen.getByLabelText('Username or email'), 'alice')
    await userEvent.type(screen.getByLabelText('Password'), 'correct-horse')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent(/^\/$/))
  })
})
