import { ChevronRight, PackageOpen, Plus } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router'
import { useMyProducts } from '@/api/queries'
import { PRODUCT_STATUSES, type ProductStatus } from '@/api/types'
import { PageHeader } from '@/components/layout/PageHeader'
import { CsvImport } from '@/components/product/CsvImport'
import { Countdown } from '@/components/product/Countdown'
import { ProductArt } from '@/components/product/ProductArt'
import { StatusBadge } from '@/components/product/StatusBadge'
import { STATUS_META } from '@/components/product/status'
import { buttonClasses } from '@/components/ui/buttonStyles'
import { Card, CardHeader } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import { EmptyState, ErrorState } from '@/components/ui/States'
import { cn } from '@/lib/cn'
import { formatPrice } from '@/lib/format'

type Filter = ProductStatus | 'all'

export function MyListingsPage() {
  const { data, isPending, isError, error, refetch } = useMyProducts()
  const [filter, setFilter] = useState<Filter>('all')

  const counts = useMemo(() => {
    const result: Record<string, number> = { all: data?.length ?? 0 }
    for (const p of data ?? []) result[p.status] = (result[p.status] ?? 0) + 1
    return result
  }, [data])

  const visible = useMemo(
    () => [...(data ?? [])].filter((p) => filter === 'all' || p.status === filter).sort((a, b) => b.id - a.id),
    [data, filter],
  )

  const filters: Filter[] = ['all', ...PRODUCT_STATUSES.filter((s) => counts[s])]

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Selling"
        title="My listings"
        description="Track your drafts, live auctions and completed sales."
        action={
          <Link to="/sell" className={buttonClasses({ variant: 'brand' })}>
            <Plus className="size-4" aria-hidden /> New listing
          </Link>
        }
      />

      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_340px] lg:items-start">
        <section aria-label="Your listings" className="space-y-4">
          {data && data.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {filters.map((f) => (
                <button
                  key={f}
                  type="button"
                  aria-pressed={filter === f}
                  onClick={() => setFilter(f)}
                  className={cn(
                    'rounded-full px-3 py-1 text-sm font-medium ring-1 transition-colors ring-inset',
                    filter === f ? 'bg-stone-900 text-white ring-stone-900' : 'bg-white text-stone-600 ring-stone-200 hover:bg-stone-50',
                  )}
                >
                  {f === 'all' ? 'All' : STATUS_META[f].label} <span className="ml-1 tabular opacity-70">{counts[f] ?? 0}</span>
                </button>
              ))}
            </div>
          )}

          {isPending ? (
            <div className="space-y-3">
              {Array.from({ length: 4 }, (_, i) => (
                <Skeleton key={i} className="h-24 rounded-2xl" />
              ))}
            </div>
          ) : isError ? (
            <ErrorState title="Could not load your listings" error={error} onRetry={() => refetch()} />
          ) : data.length === 0 ? (
            <EmptyState
              icon={PackageOpen}
              title="You haven't listed anything yet"
              description="Create your first listing, or import several at once from a CSV file."
              action={<Link to="/sell" className={buttonClasses({ variant: 'brand' })}>Create a listing</Link>}
            />
          ) : (
            <ul className="space-y-3">
              {visible.map((product) => (
                <li key={product.id}>
                  <Link
                    to={`/products/${product.id}`}
                    className="group flex items-center gap-4 rounded-2xl bg-white p-3 shadow-card ring-1 ring-stone-200/80 transition hover:shadow-lift sm:p-4"
                  >
                    <ProductArt id={product.id} name={product.name} className="size-16 shrink-0 rounded-xl [&_span]:text-xl sm:size-20" />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <StatusBadge status={product.status} />
                        <span className="text-xs text-stone-500">Lot #{product.id}</span>
                      </div>
                      <p className="mt-1 truncate font-medium text-stone-900">{product.name}</p>
                      <p className="text-sm text-stone-500">
                        <span className="font-medium text-stone-700 tabular">{formatPrice(product.current_price)}</span>
                        {product.status === 'active' && product.auction_ends_at && (
                          <>
                            {' · '}
                            <Countdown endsAt={product.auction_ends_at} compact />
                          </>
                        )}
                        {product.status === 'closed' && ' · Awaiting your decision'}
                      </p>
                    </div>
                    <ChevronRight className="size-5 shrink-0 text-stone-300 transition group-hover:translate-x-0.5 group-hover:text-stone-500" aria-hidden />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <Card>
          <CardHeader title="Bulk import" description="Create many drafts from one CSV file." />
          <div className="p-5 sm:p-6">
            <CsvImport />
          </div>
        </Card>
      </div>
    </div>
  )
}
