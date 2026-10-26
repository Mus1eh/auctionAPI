import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { tokenStore } from '@/api/tokens'
import type { Product } from '@/api/types'
import { fakeJwt, jsonResponse, mockFetch, renderApp } from '@/test/utils'
import { BidPanel } from './BidPanel'

const product: Product = {
  id: 7,
  name: 'Camera',
  description: null,
  start_price: 100,
  current_price: 150,
  owner_id: 1,
  status: 'active',
  auction_started_at: new Date(Date.now() - 60_000).toISOString(),
  auction_ends_at: new Date(Date.now() + 3_600_000).toISOString(),
}

const signedIn = {
  'POST /auth/refresh': { access_token: fakeJwt('bidder'), refresh_token: 'r2', token_type: 'bearer' },
  'GET /admin/dashboard': jsonResponse({}, 403),
}

describe('BidPanel', () => {
  it('asks anonymous visitors to sign in', () => {
    mockFetch({})
    renderApp(<BidPanel product={product} isOwner={false} bidCount={2} />, { route: '/products/7', path: '/products/:id' })
    expect(screen.getByRole('link', { name: /sign in to bid/i })).toHaveAttribute('href', '/login?next=%2Fproducts%2F7')
  })

  it('prevents owners from bidding', async () => {
    tokenStore.setTokens({ access_token: 'x', refresh_token: 'r1' })
    mockFetch(signedIn)
    renderApp(<BidPanel product={product} isOwner bidCount={0} />)
    expect(await screen.findByText(/can’t bid on it/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /place bid/i })).not.toBeInTheDocument()
  })

  it('validates and submits a bid amount', async () => {
    tokenStore.setTokens({ access_token: 'x', refresh_token: 'r1' })
    const fetchMock = mockFetch({
      ...signedIn,
      'POST /bids/7': jsonResponse({ id: 1, product_id: 7, user_id: 2, amount: 160, created_at: new Date().toISOString() }, 201),
      'GET /products/status/active': [],
    })
    renderApp(<BidPanel product={product} isOwner={false} bidCount={2} />)
    const input = await screen.findByLabelText('Your bid')

    await userEvent.type(input, '150')
    await userEvent.click(screen.getByRole('button', { name: /place bid/i }))
    expect(await screen.findByText('Bid must be greater than 150')).toBeInTheDocument()

    await userEvent.clear(input)
    await userEvent.type(input, '160')
    await userEvent.click(screen.getByRole('button', { name: /place bid/i }))
    await waitFor(() => expect(fetchMock.mock.calls.some(([url]) => String(url) === '/api/bids/7')).toBe(true))
    const bidCall = fetchMock.mock.calls.find(([url]) => String(url) === '/api/bids/7')!
    expect(bidCall[1]?.body).toBe(JSON.stringify({ amount: 160 }))
  })

  it('shows the backend conflict message when outbid', async () => {
    tokenStore.setTokens({ access_token: 'x', refresh_token: 'r1' })
    mockFetch({
      ...signedIn,
      'POST /bids/7': jsonResponse({ detail: 'Bid amount must be greater than the current price of 200' }, 409),
    })
    renderApp(<BidPanel product={product} isOwner={false} bidCount={2} />)
    await userEvent.click(await screen.findByRole('button', { name: '152' }))
    await userEvent.click(screen.getByRole('button', { name: /place bid/i }))
    expect(await screen.findByText('Bid amount must be greater than the current price of 200')).toBeInTheDocument()
  })

  it('shows no bid form once the auction has ended', () => {
    mockFetch({})
    renderApp(<BidPanel product={{ ...product, status: 'sold' }} isOwner={false} bidCount={3} />)
    expect(screen.getByText('Sold for')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /place bid/i })).not.toBeInTheDocument()
  })
})
