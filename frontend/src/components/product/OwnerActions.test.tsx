import { screen } from '@testing-library/react'
import { tokenStore } from '@/api/tokens'
import type { Bid, Product } from '@/api/types'
import { useAuth } from '@/auth/AuthContext'
import { fakeJwt, jsonResponse, mockFetch, renderApp } from '@/test/utils'
import { ManageListing } from './OwnerActions'

const product: Product = {
  id: 7,
  name: 'Camera',
  description: null,
  start_price: 100,
  current_price: 150,
  owner_id: 1,
  status: 'closed',
  auction_started_at: new Date(Date.now() - 7_200_000).toISOString(),
  auction_ends_at: new Date(Date.now() - 3_600_000).toISOString(),
}

const topBid: Bid = { id: 3, product_id: 7, user_id: 2, amount: 150, created_at: new Date().toISOString() }

function SessionReady() {
  const { status } = useAuth()
  return status === 'authenticated' ? <p>session ready</p> : null
}

function signInAs(role: 'admin' | 'superadmin') {
  tokenStore.setTokens({ access_token: 'x', refresh_token: 'r1' })
  mockFetch({
    'POST /auth/refresh': { access_token: fakeJwt('staff'), refresh_token: 'r2', token_type: 'bearer' },
    'GET /admin/dashboard': jsonResponse({ message: 'Welcome', username: 'staff', role }),
  })
}

function renderListing(isOwner: boolean) {
  renderApp(
    <>
      <SessionReady />
      <ManageListing product={product} isOwner={isOwner} topBid={topBid} />
    </>,
    { route: '/products/7', path: '/products/:id' },
  )
}

describe('ManageListing bid decision', () => {
  afterEach(() => {
    tokenStore.clear()
    vi.unstubAllGlobals()
  })

  it('shows the decision to a superadmin who does not own the listing', async () => {
    signInAs('superadmin')
    renderListing(false)
    expect(await screen.findByRole('button', { name: /accept & sell/i })).toBeInTheDocument()
  })

  it('hides the decision from an admin who does not own the listing', async () => {
    signInAs('admin')
    renderListing(false)
    await screen.findByText('session ready')
    expect(screen.queryByRole('button', { name: /accept & sell/i })).not.toBeInTheDocument()
  })
})
