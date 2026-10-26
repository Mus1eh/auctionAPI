import { PackageOpen, Search, SearchX } from 'lucide-react'
import { useMemo } from 'react'
import { Link, useSearchParams } from 'react-router'
import { useProductsByStatus } from '@/api/queries'
import { PRODUCT_STATUSES, type ProductStatus } from '@/api/types'
import { useAuth } from '@/auth/AuthContext'
import { ProductCard, ProductCardSkeleton } from '@/components/product/ProductCard'
import { STATUS_META } from '@/components/product/status'
import { Button } from '@/components/ui/Button'
import { buttonClasses } from '@/components/ui/buttonStyles'
import { Input, Select } from '@/components/ui/Field'
import { EmptyState, ErrorState } from '@/components/ui/States'
import { cn } from '@/lib/cn'
import { filterAndSortProducts, SORT_OPTIONS, type SortKey } from '@/lib/products'

const TAB_LABELS: Record<ProductStatus, string> = {
  active: 'Live now',
  draft: 'Drafts',
  closed: 'Ended',
  sold: 'Sold',
  rejected: 'Bid declined',
}

function isStatus(value: string | null): value is ProductStatus {
  return PRODUCT_STATUSES.includes(value as ProductStatus)
}

function isSort(value: string | null): value is SortKey {
  return SORT_OPTIONS.some((o) => o.value === value)
}

export function MarketplacePage() {
  const { status: authStatus } = useAuth()
  const [params, setParams] = useSearchParams()
  const statusParam = params.get('status')
  const status: ProductStatus = isStatus(statusParam) ? statusParam : 'active'
  const query = params.get('q') ?? ''
  const sortParam = params.get('sort')
  const sort: SortKey = isSort(sortParam) ? sortParam : status === 'active' ? 'ending' : 'newest'

  const { data, isPending, isError, error, refetch, isFetching } = useProductsByStatus(status)
  const products = useMemo(() => filterAndSortProducts(data ?? [], query, sort), [data, query, sort])

  const update = (changes: Record<string, string | null>) => {
    const next = new URLSearchParams(params)
    for (const [key, value] of Object.entries(changes)) {
      if (value) next.set(key, value)
      else next.delete(key)
    }
    setParams(next, { replace: true })
  }

  return (
    <div className="space-y-8">
      <section className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-2xl">
          <p className="text-sm font-medium text-brand-700">The marketplace</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight text-balance text-stone-900 sm:text-4xl">
            Bid on one-of-a-kind finds, in real time.
          </h1>
          <p className="mt-3 text-base text-stone-600">
            Every approved lot runs a one-hour auction. The highest bid when the clock stops goes to the seller for approval.
          </p>
        </div>
        {authStatus !== 'authenticated' && authStatus !== 'loading' && (
          <div className="flex gap-2">
            <Link to="/register" className={buttonClasses({ variant: 'primary' })}>
              Start bidding
            </Link>
            <Link to="/login?next=%2Fsell" className={buttonClasses({ variant: 'secondary' })}>
              Sell an item
            </Link>
          </div>
        )}
      </section>

      <section aria-label="Listings" className="space-y-5">
        <div className="flex flex-col gap-3 border-b border-stone-200 pb-4 lg:flex-row lg:items-center lg:justify-between">
          <div role="tablist" aria-label="Listing status" className="-mx-1 flex gap-1 overflow-x-auto px-1 pb-1 lg:pb-0">
            {PRODUCT_STATUSES.map((s) => (
              <button
                key={s}
                role="tab"
                type="button"
                aria-selected={s === status}
                onClick={() => update({ status: s === 'active' ? null : s, sort: null })}
                className={cn(
                  'inline-flex shrink-0 items-center gap-2 rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors',
                  s === status ? 'bg-stone-900 text-white' : 'text-stone-600 hover:bg-stone-100 hover:text-stone-900',
                )}
              >
                {s === 'active' && <span className={cn('size-1.5 rounded-full', s === status ? 'bg-brand-300' : 'bg-brand-500')} />}
                {TAB_LABELS[s]}
                {s === status && data && <span className="rounded-full bg-white/20 px-1.5 text-xs tabular">{data.length}</span>}
              </button>
            ))}
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <div className="relative sm:w-72">
              <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-stone-400" aria-hidden />
              <Input
                type="search"
                aria-label="Search listings"
                placeholder="Search by name or description"
                value={query}
                onChange={(e) => update({ q: e.target.value || null })}
                className="pl-9"
              />
            </div>
            <Select aria-label="Sort listings" value={sort} onChange={(e) => update({ sort: e.target.value })} className="sm:w-48">
              {SORT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </Select>
          </div>
        </div>

        <p className="text-sm text-stone-500" aria-live="polite">
          {isPending
            ? 'Loading listings…'
            : isError
              ? null
              : `${products.length} ${products.length === 1 ? 'listing' : 'listings'} · ${STATUS_META[status].description}${isFetching ? ' · Updating…' : ''}`}
        </p>

        {isPending ? (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {Array.from({ length: 8 }, (_, i) => (
              <ProductCardSkeleton key={i} />
            ))}
          </div>
        ) : isError ? (
          <ErrorState title="Could not load listings" error={error} onRetry={() => refetch()} />
        ) : products.length === 0 ? (
          query ? (
            <EmptyState
              icon={SearchX}
              title="No matching listings"
              description={`Nothing in “${TAB_LABELS[status]}” matches “${query}”.`}
              action={
                <Button variant="secondary" onClick={() => update({ q: null })}>
                  Clear search
                </Button>
              }
            />
          ) : (
            <EmptyState
              icon={PackageOpen}
              title={status === 'active' ? 'No live auctions right now' : `No listings in “${TAB_LABELS[status]}”`}
              description={status === 'active' ? 'New lots go live as soon as an admin approves them. Check back soon.' : undefined}
              action={
                authStatus === 'authenticated' ? (
                  <Link to="/sell" className={buttonClasses({ variant: 'brand' })}>
                    List an item
                  </Link>
                ) : undefined
              }
            />
          )
        ) : (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
