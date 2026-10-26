import { Link } from 'react-router'
import type { Product } from '@/api/types'
import { formatDateTime, formatPrice } from '@/lib/format'
import { Countdown } from './Countdown'
import { ProductArt } from './ProductArt'
import { StatusBadge } from './StatusBadge'

export function ProductCard({ product }: { product: Product }) {
  const raised = product.current_price > product.start_price

  return (
    <article className="group relative flex flex-col overflow-hidden rounded-2xl bg-white shadow-card ring-1 ring-stone-200/80 transition hover:-translate-y-0.5 hover:shadow-lift">
      <div className="relative">
        <ProductArt id={product.id} name={product.name} className="aspect-[4/3]" />
        <div className="absolute top-3 left-3">
          <StatusBadge status={product.status} className="bg-white/90 backdrop-blur" />
        </div>
      </div>
      <div className="flex flex-1 flex-col p-4">
        <h3 className="line-clamp-1 font-semibold text-stone-900">
          <Link to={`/products/${product.id}`} className="after:absolute after:inset-0 focus-visible:outline-none">
            {product.name}
          </Link>
        </h3>
        <p className="mt-1 line-clamp-2 min-h-10 text-sm text-stone-500">{product.description || 'No description provided.'}</p>
        <div className="mt-4 flex items-end justify-between gap-3 border-t border-stone-100 pt-3">
          <div>
            <p className="text-xs text-stone-500">{raised ? 'Current bid' : 'Starting price'}</p>
            <p className="text-lg font-semibold tabular text-stone-900">{formatPrice(product.current_price)}</p>
          </div>
          <div className="text-right text-xs">
            {product.status === 'active' && product.auction_ends_at ? (
              <Countdown endsAt={product.auction_ends_at} compact className="font-medium" />
            ) : product.auction_ends_at ? (
              <span className="text-stone-500">Ended {formatDateTime(product.auction_ends_at)}</span>
            ) : (
              <span className="text-stone-500">Lot #{product.id}</span>
            )}
          </div>
        </div>
      </div>
    </article>
  )
}

export function ProductCardSkeleton() {
  return (
    <div className="overflow-hidden rounded-2xl bg-white shadow-card ring-1 ring-stone-200/80">
      <div className="aspect-[4/3] animate-pulse bg-stone-200/70" />
      <div className="space-y-2 p-4">
        <div className="h-4 w-2/3 animate-pulse rounded bg-stone-200/70" />
        <div className="h-3 w-full animate-pulse rounded bg-stone-200/70" />
        <div className="h-3 w-4/5 animate-pulse rounded bg-stone-200/70" />
        <div className="mt-4 h-6 w-1/3 animate-pulse rounded bg-stone-200/70" />
      </div>
    </div>
  )
}
