import { ArrowLeft, PackageX } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams } from 'react-router'
import { isApiError } from '@/api/client'
import { useBids, useMyProducts, useProduct } from '@/api/queries'
import { useAuth } from '@/auth/AuthContext'
import { AdminControls } from '@/components/product/AdminControls'
import { BidHistory } from '@/components/product/BidHistory'
import { BidPanel } from '@/components/product/BidPanel'
import { Countdown } from '@/components/product/Countdown'
import { ManageListing } from '@/components/product/OwnerActions'
import { ProductArt } from '@/components/product/ProductArt'
import { StatusBadge } from '@/components/product/StatusBadge'
import { STATUS_META } from '@/components/product/status'
import { buttonClasses } from '@/components/ui/buttonStyles'
import { Card } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import { EmptyState, ErrorState } from '@/components/ui/States'
import { formatDateTime, formatPrice } from '@/lib/format'

function DetailSkeleton() {
  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_400px]">
      <Skeleton className="aspect-[4/3] rounded-2xl" />
      <div className="space-y-4">
        <Skeleton className="h-8 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-48 rounded-2xl" />
      </div>
    </div>
  )
}

export function ProductDetailPage() {
  const id = Number(useParams().id)
  const { status: authStatus, isAdmin } = useAuth()
  const [bidPage, setBidPage] = useState(1)
  const { data: product, isPending, isError, error, refetch } = useProduct(id)
  const myProducts = useMyProducts(authStatus === 'authenticated')
  const live = product?.status === 'active'
  // Page 1 of bids is shared with BidHistory's cache; used for the bid count and the top bid.
  const firstPage = useBids(id, 1, live)

  if (!Number.isInteger(id) || id <= 0 || isApiError(error, 404)) {
    return (
      <EmptyState
        icon={PackageX}
        title="Listing not found"
        description="It may have been removed by its seller."
        action={<Link to="/" className={buttonClasses({ variant: 'secondary' })}>Browse the marketplace</Link>}
        className="my-10"
      />
    )
  }
  if (isPending) return <DetailSkeleton />
  if (isError) return <ErrorState title="Could not load this listing" error={error} onRetry={() => refetch()} />

  const isOwner = myProducts.data?.some((p) => p.id === product.id) ?? false
  // The API exposes no "current user" id; it can be inferred from any owned product.
  const myUserId = myProducts.data?.[0]?.owner_id ?? null
  const canManage = isOwner || isAdmin
  const meta = STATUS_META[product.status]

  return (
    <div className="space-y-8">
      <Link to="/" className="inline-flex items-center gap-1.5 text-sm font-medium text-stone-600 hover:text-stone-900">
        <ArrowLeft className="size-4" aria-hidden /> Marketplace
      </Link>

      {/* Mobile order: details → bid panel → history. Desktop: panel sticks in the right column. */}
      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_400px] lg:items-start">
        <div className="space-y-8 lg:col-start-1">
          <ProductArt id={product.id} name={product.name} size="lg" className="aspect-[16/10] rounded-2xl ring-1 ring-stone-200/80 lg:aspect-[2/1]" />

          <div>
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge status={product.status} />
              <span className="text-sm text-stone-500">Lot #{product.id}</span>
              {isOwner && <span className="rounded-full bg-sky-50 px-2 py-0.5 text-xs font-medium text-sky-700 ring-1 ring-sky-200 ring-inset">Your listing</span>}
            </div>
            <h1 className="mt-3 text-2xl font-semibold tracking-tight text-stone-900 sm:text-3xl">{product.name}</h1>
            <p className="mt-4 max-w-prose leading-relaxed whitespace-pre-line text-stone-600">
              {product.description || 'The seller has not added a description.'}
            </p>
          </div>

          <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-2xl bg-stone-200/80 ring-1 ring-stone-200/80 sm:grid-cols-4">
            {[
              ['Starting price', formatPrice(product.start_price)],
              ['Seller', isOwner ? 'You' : `Seller #${product.owner_id}`],
              ['Auction started', formatDateTime(product.auction_started_at)],
              [product.status === 'active' ? 'Ends' : 'Ended', formatDateTime(product.auction_ends_at)],
            ].map(([label, value]) => (
              <div key={label} className="bg-white p-4">
                <dt className="text-xs text-stone-500">{label}</dt>
                <dd className="mt-1 text-sm font-medium text-stone-900 tabular">{value}</dd>
              </div>
            ))}
          </dl>
        </div>

        <aside className="space-y-4 lg:sticky lg:top-24 lg:col-start-2 lg:row-span-2 lg:row-start-1">
          <Card className="p-5 sm:p-6">
            <div className="mb-5 flex items-center justify-between gap-2 border-b border-stone-100 pb-4">
              <span className="text-sm font-medium text-stone-700">{meta.description}</span>
              {product.status === 'active' && product.auction_ends_at && <Countdown endsAt={product.auction_ends_at} compact className="text-sm font-semibold" />}
            </div>
            <BidPanel product={product} isOwner={isOwner} bidCount={firstPage.data?.length ?? null} />
          </Card>
          {canManage && (
            <Card className="space-y-4 p-5 sm:p-6">
              <h2 className="text-sm font-semibold text-stone-900">{isOwner ? 'Manage your listing' : 'Manage listing'}</h2>
              <ManageListing product={product} isOwner={isOwner} topBid={firstPage.data?.[0]} />
              {isAdmin && <AdminControls product={product} />}
            </Card>
          )}
        </aside>

        <div className="lg:col-start-1">
          <BidHistory productId={product.id} live={live} page={bidPage} onPageChange={setBidPage} myUserId={myUserId} />
        </div>
      </div>
    </div>
  )
}
