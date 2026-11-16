import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { jsonResponse, mockFetch, renderApp } from '@/test/utils'
import { RequestRestorePage } from './RequestRestorePage'
import { RestoreAccountPage } from './RestoreAccountPage'

afterEach(() => vi.unstubAllGlobals())

describe('RequestRestorePage', () => {
  it('validates the email before calling the API', async () => {
    const fetchMock = mockFetch({})
    renderApp(<RequestRestorePage />)
    await userEvent.type(screen.getByLabelText('Email'), 'not-an-email')
    await userEvent.click(screen.getByRole('button', { name: 'Send restore link' }))
    expect(await screen.findByText('Enter a valid email address')).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('posts the email and shows the generic confirmation', async () => {
    const fetchMock = mockFetch({
      'POST /users/restore-request': jsonResponse({ message: 'If the email exists, an account restore link will be sent.' }, 202),
    })
    renderApp(<RequestRestorePage />)
    await userEvent.type(screen.getByLabelText('Email'), 'alice@example.com')
    await userEvent.click(screen.getByRole('button', { name: 'Send restore link' }))
    expect(await screen.findByText('Check your inbox')).toBeInTheDocument()
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual({ email: 'alice@example.com' })
  })

  it('shows a friendly message when rate limited', async () => {
    mockFetch({ 'POST /users/restore-request': jsonResponse({ detail: 'Too many requests' }, 429) })
    renderApp(<RequestRestorePage />)
    await userEvent.type(screen.getByLabelText('Email'), 'alice@example.com')
    await userEvent.click(screen.getByRole('button', { name: 'Send restore link' }))
    expect(await screen.findByText('Too many requests. Please try again later.')).toBeInTheDocument()
  })
})

describe('RestoreAccountPage', () => {
  it('points to the request page when the link has no token', () => {
    mockFetch({})
    renderApp(<RestoreAccountPage />, { route: '/restore-account', path: '/restore-account' })
    expect(screen.getByText('Missing restore link')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Request a restore link' })).toHaveAttribute('href', '/restore-request')
  })

  it('does not call the API until the user confirms, then restores', async () => {
    const fetchMock = mockFetch({
      'POST /users/restore': { message: 'Your account has been restored. You can log in now.' },
    })
    renderApp(<RestoreAccountPage />, { route: '/restore-account?token=abc123', path: '/restore-account' })
    expect(fetchMock).not.toHaveBeenCalled()
    await userEvent.click(screen.getByRole('button', { name: 'Restore my account' }))
    expect(await screen.findByText('Account restored')).toBeInTheDocument()
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual({ token: 'abc123' })
    expect(screen.getByRole('link', { name: 'Sign in' })).toHaveAttribute('href', '/login')
  })

  it('shows the server error and offers a new link when the token is rejected', async () => {
    mockFetch({ 'POST /users/restore': jsonResponse({ detail: 'Invalid or expired token' }, 400) })
    renderApp(<RestoreAccountPage />, { route: '/restore-account?token=bad', path: '/restore-account' })
    await userEvent.click(screen.getByRole('button', { name: 'Restore my account' }))
    expect(await screen.findByText('This restore link can’t be used')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByRole('link', { name: 'Request a new link' })).toHaveAttribute('href', '/restore-request'))
  })
})
