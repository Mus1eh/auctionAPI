import type { Product } from '@/api/types'
import { filterAndSortProducts, suggestedBids } from './products'

const product = (id: number, overrides: Partial<Product> = {}): Product => ({
  id,
  name: `Item ${id}`,
  description: null,
  start_price: 10,
  current_price: 10,
  owner_id: 1,
  status: 'active',
  ...overrides,
})

describe('filterAndSortProducts', () => {
  const items = [
    product(1, { name: 'Vintage camera', current_price: 300, auction_ends_at: '2026-01-01T12:30:00Z' }),
    product(2, { name: 'Oak table', description: 'Solid oak, camera not included', current_price: 50, auction_ends_at: '2026-01-01T12:10:00Z' }),
    product(3, { name: 'Lamp', current_price: 120 }),
  ]

  it('searches name and description case-insensitively', () => {
    expect(filterAndSortProducts(items, 'CAMERA', 'newest').map((p) => p.id)).toEqual([2, 1])
  })

  it('sorts by ending soonest with undated items last', () => {
    expect(filterAndSortProducts(items, '', 'ending').map((p) => p.id)).toEqual([2, 1, 3])
  })

  it('sorts by price both ways', () => {
    expect(filterAndSortProducts(items, '', 'price-desc').map((p) => p.id)).toEqual([1, 3, 2])
    expect(filterAndSortProducts(items, '', 'price-asc').map((p) => p.id)).toEqual([2, 3, 1])
  })

  it('does not mutate the input', () => {
    const copy = [...items]
    filterAndSortProducts(items, '', 'price-asc')
    expect(items).toEqual(copy)
  })
})

describe('suggestedBids', () => {
  it('suggests +1%, +5% and +10% rounded up', () => {
    expect(suggestedBids(1000)).toEqual([1010, 1050, 1100])
  })

  it('always increases by at least 1 and de-duplicates', () => {
    expect(suggestedBids(5)).toEqual([6])
  })
})
