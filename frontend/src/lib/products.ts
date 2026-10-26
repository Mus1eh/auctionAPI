import type { Product } from '@/api/types'

export type SortKey = 'ending' | 'newest' | 'price-desc' | 'price-asc'

export const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: 'ending', label: 'Ending soonest' },
  { value: 'newest', label: 'Newest listings' },
  { value: 'price-desc', label: 'Price: high to low' },
  { value: 'price-asc', label: 'Price: low to high' },
]

/** Client-side search and sort: the API only filters by status. */
export function filterAndSortProducts(products: Product[], query: string, sort: SortKey) {
  const q = query.trim().toLowerCase()
  const filtered = q
    ? products.filter((p) => p.name.toLowerCase().includes(q) || (p.description ?? '').toLowerCase().includes(q))
    : [...products]

  const endTime = (p: Product) => (p.auction_ends_at ? new Date(p.auction_ends_at).getTime() : Number.POSITIVE_INFINITY)

  return filtered.sort((a, b) => {
    switch (sort) {
      case 'ending':
        return endTime(a) - endTime(b) || b.id - a.id
      case 'price-desc':
        return b.current_price - a.current_price || b.id - a.id
      case 'price-asc':
        return a.current_price - b.current_price || b.id - a.id
      default:
        return b.id - a.id
    }
  })
}

/** Quick-bid amounts: +1%, +5% and +10% over the current price, each at least +1. */
export function suggestedBids(currentPrice: number) {
  const steps = [0.01, 0.05, 0.1].map((pct) => currentPrice + Math.max(1, Math.ceil(currentPrice * pct)))
  return [...new Set(steps)]
}
