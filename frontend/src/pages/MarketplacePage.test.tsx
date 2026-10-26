import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { jsonResponse, mockFetch, renderApp } from '@/test/utils'
import { MarketplacePage } from './MarketplacePage'

const soon = new Date(Date.now() + 600_000).toISOString()
const later = new Date(Date.now() + 3_000_000).toISOString()

describe('MarketplacePage', () => {
  it('lists live auctions, ending soonest first, and filters by search', async () => {
    mockFetch({
      'GET /products/status/active': [
        { id: 1, name: 'Oak table', description: 'Solid oak', start_price: 50, current_price: 80, owner_id: 2, status: 'active', auction_ends_at: later },
        { id: 2, name: 'Film camera', description: null, start_price: 30, current_price: 30, owner_id: 3, status: 'active', auction_ends_at: soon },
      ],
    })
    renderApp(<MarketplacePage />)
    const cards = await screen.findAllByRole('article')
    expect(cards.map((c) => within(c).getByRole('heading').textContent)).toEqual(['Film camera', 'Oak table'])
    expect(screen.getByText('2 listings · Accepting bids now')).toBeInTheDocument()

    await userEvent.type(screen.getByLabelText('Search listings'), 'oak')
    expect(screen.getAllByRole('article')).toHaveLength(1)
    expect(screen.getByTestId('location')).toHaveTextContent('/?q=oak')
  })

  it('switches status tabs and requests that status', async () => {
    const fetchMock = mockFetch({
      'GET /products/status/active': [],
      'GET /products/status/sold': [{ id: 5, name: 'Clock', description: null, start_price: 10, current_price: 99, owner_id: 2, status: 'sold' }],
    })
    renderApp(<MarketplacePage />)
    expect(await screen.findByText('No live auctions right now')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('tab', { name: /sold/i }))
    expect(await screen.findByText('Clock')).toBeInTheDocument()
    expect(fetchMock.mock.calls.map(([u]) => String(u))).toContain('/api/products/status/sold')
  })

  it('shows an error state with retry when the API fails', async () => {
    mockFetch({ 'GET /products/status/active': new Response('Internal Server Error', { status: 500 }) })
    renderApp(<MarketplacePage />)
    expect(await screen.findByText('Could not load listings')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
  })

  it('treats a 404 list response as empty', async () => {
    mockFetch({ 'GET /products/status/active': jsonResponse({ detail: 'No products found.' }, 404) })
    renderApp(<MarketplacePage />)
    expect(await screen.findByText('No live auctions right now')).toBeInTheDocument()
  })
})
