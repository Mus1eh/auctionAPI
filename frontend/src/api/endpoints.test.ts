import { jsonResponse, mockFetch } from '@/test/utils'
import { adminApi, authApi, bidsApi, productsApi } from './endpoints'
import { tokenStore } from './tokens'

beforeEach(() => tokenStore.setTokens({ access_token: 'a', refresh_token: 'r' }))
afterEach(() => {
  tokenStore.clear()
  vi.unstubAllGlobals()
})

describe('endpoints', () => {
  it('logs in with an OAuth2 password form', async () => {
    const fetchMock = mockFetch({ 'POST /auth/': { access_token: 'a', refresh_token: 'r', token_type: 'bearer' } })
    await authApi.login('alice@example.com', 'secret123')
    const body = fetchMock.mock.calls[0][1]?.body as URLSearchParams
    expect(body).toBeInstanceOf(URLSearchParams)
    expect(Object.fromEntries(body)).toEqual({ grant_type: 'password', username: 'alice@example.com', password: 'secret123' })
  })

  it('lists products by status from /products/status/{status}', async () => {
    const fetchMock = mockFetch({ 'GET /products/status/sold': [{ id: 1 }] })
    await expect(productsApi.listByStatus('sold')).resolves.toEqual([{ id: 1 }])
    expect(String(fetchMock.mock.calls[0][0])).toBe('/api/products/status/sold')
  })

  it('treats 404 "nothing found" list responses as empty lists', async () => {
    mockFetch({
      'GET /products/status/closed': jsonResponse({ detail: 'No products found.' }, 404),
      'GET /products/my': jsonResponse({ detail: 'You have no products.' }, 404),
    })
    await expect(productsApi.listByStatus('closed')).resolves.toEqual([])
    await expect(productsApi.mine()).resolves.toEqual([])
  })

  it('does not hide server errors on list endpoints', async () => {
    mockFetch({ 'GET /products/status/active': new Response('Internal Server Error', { status: 500 }) })
    await expect(productsApi.listByStatus('active')).rejects.toMatchObject({ status: 500 })
  })

  it('sends the go-live request as a query parameter', async () => {
    const fetchMock = mockFetch({ 'POST /products/4/status-request': jsonResponse({ id: 9 }, 201) })
    await productsApi.requestStatus(4, 'active')
    expect(String(fetchMock.mock.calls[0][0])).toBe('/api/products/4/status-request?request=active')
  })

  it('sends bid decisions as a query parameter', async () => {
    const fetchMock = mockFetch({ 'POST /bids/4/approve': { id: 4, winning_bidder: null } })
    await bidsApi.decide(4, 'reject')
    expect(String(fetchMock.mock.calls[0][0])).toBe('/api/bids/4/approve?request=reject')
  })

  it('paginates bids with page and limit', async () => {
    const fetchMock = mockFetch({ 'GET /bids/4': [] })
    await bidsApi.list(4, 3)
    expect(String(fetchMock.mock.calls[0][0])).toBe('/api/bids/4?page=3&limit=10')
  })

  it('uploads CSV files as multipart form data', async () => {
    const fetchMock = mockFetch({ 'POST /products/import-csv': jsonResponse({ message: 'ok', imported_count: 2 }, 201) })
    const file = new File(['name,description,start_price\nA,,1'], 'items.csv', { type: 'text/csv' })
    await productsApi.importCsv(file)
    const [, init] = fetchMock.mock.calls[0]
    expect((init?.body as FormData).get('file')).toBeInstanceOf(File)
    expect(init?.headers).not.toHaveProperty('Content-Type')
  })

  it('changes roles with a JSON role_name body', async () => {
    const fetchMock = mockFetch({ 'PATCH /admin/users/5/role': { id: 5, username: 'x', email: 'x@example.com' } })
    await adminApi.changeUserRole(5, 'admin')
    expect(fetchMock.mock.calls[0][1]?.body).toBe(JSON.stringify({ role_name: 'admin' }))
  })
})
