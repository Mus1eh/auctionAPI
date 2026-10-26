import { fakeJwt, jsonResponse, mockFetch } from '@/test/utils'
import { ApiError, apiRequest, buildUrl, messageFromDetail } from './client'
import { tokenStore } from './tokens'

beforeEach(() => tokenStore.clear())
afterEach(() => vi.unstubAllGlobals())

describe('buildUrl', () => {
  it('prefixes the base URL and drops undefined query values', () => {
    expect(buildUrl('/bids/3', { page: 2, limit: undefined })).toBe('/api/bids/3?page=2')
    expect(buildUrl('/products/')).toBe('/api/products/')
  })
})

describe('messageFromDetail', () => {
  it('handles string, validation array and object details', () => {
    expect(messageFromDetail('Product is not found.', 'x')).toBe('Product is not found.')
    expect(
      messageFromDetail([{ loc: ['body', 'amount'], msg: 'Input should be greater than 0', type: 'greater_than' }], 'x'),
    ).toBe('amount: Input should be greater than 0')
    expect(messageFromDetail({ message: 'CSV validation failed', errors: [] }, 'x')).toBe('CSV validation failed')
    expect(messageFromDetail(undefined, 'fallback')).toBe('fallback')
  })
})

describe('apiRequest', () => {
  it('sends JSON with the bearer token for authenticated requests', async () => {
    tokenStore.setTokens({ access_token: 'access-1', refresh_token: 'refresh-1' })
    const fetchMock = mockFetch({ 'POST /bids/7': jsonResponse({ id: 1 }, 201) })

    await apiRequest('/bids/7', { method: 'POST', auth: true, json: { amount: 50 } })

    const [, init] = fetchMock.mock.calls[0]
    expect(init?.headers).toMatchObject({ Authorization: 'Bearer access-1', 'Content-Type': 'application/json' })
    expect(init?.body).toBe(JSON.stringify({ amount: 50 }))
  })

  it('does not attach a token to public requests', async () => {
    tokenStore.setTokens({ access_token: 'access-1', refresh_token: 'refresh-1' })
    const fetchMock = mockFetch({ 'GET /products/1': { id: 1 } })
    await apiRequest('/products/1')
    expect(fetchMock.mock.calls[0][1]?.headers).not.toHaveProperty('Authorization')
  })

  it('throws ApiError with the FastAPI detail message', async () => {
    mockFetch({ 'GET /products/9': jsonResponse({ detail: 'Product is not found.' }, 404) })
    const error = await apiRequest('/products/9').catch((e) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 404, message: 'Product is not found.' })
  })

  it('exposes field errors from 422 responses', async () => {
    mockFetch({
      'POST /users/': jsonResponse({ detail: [{ loc: ['body', 'email'], msg: 'value is not a valid email address', type: 'value_error' }] }, 422),
    })
    const error = (await apiRequest('/users/', { method: 'POST', json: {} }).catch((e) => e)) as ApiError
    expect(error.fieldErrors).toEqual([{ field: 'email', message: 'value is not a valid email address' }])
  })

  it('returns undefined for 204 responses', async () => {
    mockFetch({ 'POST /auth/logout': new Response(null, { status: 204 }) })
    await expect(apiRequest('/auth/logout', { method: 'POST', json: { refresh_token: 'x' } })).resolves.toBeUndefined()
  })

  it('wraps network failures in a readable ApiError', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    await expect(apiRequest('/products/1')).rejects.toMatchObject({ status: 0, message: expect.stringContaining('Cannot reach the server') })
  })

  it('fails fast without a session for authenticated requests', async () => {
    const fetchMock = mockFetch({})
    await expect(apiRequest('/products/my', { auth: true })).rejects.toMatchObject({ status: 401 })
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('refreshes once on 401 and retries with the new token', async () => {
    tokenStore.setTokens({ access_token: 'expired', refresh_token: 'refresh-1' })
    const fetchMock = mockFetch({
      'GET /products/my': (_url, init) =>
        (init.headers as Record<string, string>).Authorization === 'Bearer fresh' ? jsonResponse([{ id: 1 }]) : jsonResponse({ detail: 'Could not validate credentials' }, 401),
      'POST /auth/refresh': jsonResponse({ access_token: 'fresh', refresh_token: 'refresh-2', token_type: 'bearer' }),
    })

    await expect(apiRequest('/products/my', { auth: true })).resolves.toEqual([{ id: 1 }])
    expect(tokenStore.getRefreshToken()).toBe('refresh-2')
    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it('shares one refresh between concurrent 401s (refresh tokens are single-use)', async () => {
    tokenStore.setTokens({ access_token: 'expired', refresh_token: 'refresh-1' })
    const fetchMock = mockFetch({
      'GET /products/my': (_url, init) =>
        (init.headers as Record<string, string>).Authorization === 'Bearer fresh' ? jsonResponse([]) : jsonResponse({}, 401),
      'POST /auth/refresh': () => jsonResponse({ access_token: 'fresh', refresh_token: 'refresh-2', token_type: 'bearer' }),
    })

    await Promise.all([apiRequest('/products/my', { auth: true }), apiRequest('/products/my', { auth: true })])
    const refreshCalls = fetchMock.mock.calls.filter(([url]) => String(url).endsWith('/auth/refresh'))
    expect(refreshCalls).toHaveLength(1)
  })

  it('clears the session when the refresh token is rejected', async () => {
    tokenStore.setTokens({ access_token: fakeJwt('bob'), refresh_token: 'revoked' })
    mockFetch({
      'GET /products/my': jsonResponse({ detail: 'Could not validate credentials' }, 401),
      'POST /auth/refresh': jsonResponse({ detail: 'Invalid refresh token' }, 401),
    })

    await expect(apiRequest('/products/my', { auth: true })).rejects.toMatchObject({ status: 401 })
    expect(tokenStore.getRefreshToken()).toBeNull()
    expect(localStorage.getItem('lotwise.refreshToken')).toBeNull()
  })
})
