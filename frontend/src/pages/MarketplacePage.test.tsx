import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { jsonResponse, mockFetch, renderApp } from '@/test/utils'
import { MarketplacePage } from './MarketplacePage'

const soon = new Date(Date.now() + 600_000).toISOString()
const later = new Date(Date.now() + 3_000_000).toISOString()

describe('MarketplacePage', () => {
  it('lists live auctions, ending soonest first, and filters by search', async () => {
    mockFetch({
      'GET /products/status/active': {
        items: [
          { id: 1, name: 'Oak table', description: 'Solid oak', start_price: 50, current_price: 80, owner_id: 2, status: 'active', auction_ends_at: later },
          { id: 2, name: 'Film camera', description: null, start_price: 30, current_price: 30, owner_id: 3, status: 'active', auction_ends_at: soon },
        ],
        total: 2,
      },
    })
    renderApp(<MarketplacePage />)
    const cards = await screen.findAllByRole('article')
    expect(cards.map((c) => within(c).getByRole('heading').textContent)).toEqual(['Film camera', 'Oak table'])
    expect(screen.getByText('2 listings · Accepting bids now')).toBeInTheDocument()

    await userEvent.type(screen.getByLabelText('Search listings on this page'), 'oak')
    expect(screen.getAllByRole('article')).toHaveLength(1)
    expect(screen.getByTestId('location')).toHaveTextContent('/?q=oak')
  })

  it('switches status tabs and requests that status', async () => {
    const fetchMock = mockFetch({
      'GET /products/status/active': { items: [], total: 0 },
      'GET /products/status/sold': {
        items: [{ id: 5, name: 'Clock', description: null, start_price: 10, current_price: 99, owner_id: 2, status: 'sold' }],
        total: 1,
      },
    })
    renderApp(<MarketplacePage />)
    expect(await screen.findByText('No live auctions right now')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('tab', { name: /sold/i }))
    expect(await screen.findByText('Clock')).toBeInTheDocument()
    expect(fetchMock.mock.calls.map(([u]) => String(u))).toContain('/api/products/status/sold?page=1&limit=20')
  })

  it('shows an error state with retry when the API fails', async () => {
    mockFetch({ 'GET /products/status/active': new Response('Internal Server Error', { status: 500 }) })
    renderApp(<MarketplacePage />)
    expect(await screen.findByText('Could not load listings')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
  })

  it('shows the empty state for an empty list', async () => {
    mockFetch({ 'GET /products/status/active': { items: [], total: 0 } })
    renderApp(<MarketplacePage />)
    expect(await screen.findByText('No live auctions right now')).toBeInTheDocument()
  })

  it('pages through listings and shows the total', async () => {
    const product = (id: number) => ({ id, name: `Lot ${id}`, description: null, start_price: 10, current_price: 10, owner_id: 2, status: 'active' })
    const fetchMock = mockFetch({
      'GET /products/status/active': (url: URL) =>
        url.searchParams.get('page') === '2'
          ? jsonResponse({ items: [product(21)], total: 21 })
          : jsonResponse({ items: [product(1)], total: 21 }),
    })
    renderApp(<MarketplacePage />)
    expect(await screen.findByText('Page 1 of 2')).toBeInTheDocument()
    expect(screen.getByText(/21 listings/)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /next/i }))
    expect(await screen.findByText('Lot 21')).toBeInTheDocument()
    expect(screen.getByText('Page 2 of 2')).toBeInTheDocument()
    expect(fetchMock.mock.calls.map(([u]) => String(u))).toContain('/api/products/status/active?page=2&limit=20')
  })
})
