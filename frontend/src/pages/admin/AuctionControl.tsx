import { PackageOpen, Play, Square } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router'
import { toast } from 'sonner'
import { useProductsByStatus, useSetProductStatus } from '@/api/queries'
import type { Product } from '@/api/types'
import { Countdown } from '@/components/product/Countdown'
import { Button } from '@/components/ui/Button'
import { Card, CardHeader } from '@/components/ui/Card'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { Skeleton } from '@/components/ui/Skeleton'
import { EmptyState, ErrorState } from '@/components/ui/States'
import { formatPrice } from '@/lib/format'

type Target = 'active' | 'closed'

function ProductList({ status, target, title, description }: { status: 'draft' | 'active'; target: Target; title: string; description: string }) {
  const { data, isPending, isError, error, refetch } = useProductsByStatus(status)
  const setStatus = useSetProductStatus()
  const [selected, setSelected] = useState<Product | null>(null)

  return (
    <Card>
      <CardHeader title={title} description={description} />
      {isPending ? (
        <div className="space-y-3 p-5">
          <Skeleton className="h-12" />
          <Skeleton className="h-12" />
        </div>
      ) : isError ? (
        <div className="p-5">
          <ErrorState error={error} onRetry={() => refetch()} />
        </div>
      ) : data.length === 0 ? (
        <div className="p-5">
          <EmptyState icon={PackageOpen} title="Nothing here" className="border-0 py-8" />
        </div>
      ) : (
        <ul className="max-h-[28rem] divide-y divide-stone-100 overflow-y-auto">
          {[...data]
            .sort((a, b) => b.id - a.id)
            .map((product) => (
              <li key={product.id} className="flex items-center gap-3 px-5 py-3 sm:px-6">
                <div className="min-w-0 flex-1">
                  <Link to={`/products/${product.id}`} className="block truncate text-sm font-medium text-stone-900 hover:underline">
                    {product.name}
                  </Link>
                  <p className="text-xs text-stone-500">
                    Lot #{product.id} · Seller #{product.owner_id} · <span className="tabular">{formatPrice(product.current_price)}</span>
                    {product.auction_ends_at && status === 'active' && (
                      <>
                        {' · '}
                        <Countdown endsAt={product.auction_ends_at} compact />
                      </>
                    )}
                  </p>
                </div>
                <Button size="sm" variant={target === 'active' ? 'secondary' : 'danger-ghost'} onClick={() => setSelected(product)}>
                  {target === 'active' ? <Play className="size-4" aria-hidden /> : <Square className="size-4" aria-hidden />}
                  {target === 'active' ? 'Start' : 'Close'}
                </Button>
              </li>
            ))}
        </ul>
      )}
      <ConfirmDialog
        open={selected !== null}
        title={target === 'active' ? `Start “${selected?.name}” now?` : `Close “${selected?.name}” early?`}
        description={
          target === 'active'
            ? 'This skips the request flow. Bidding opens immediately for one hour.'
            : 'Bidding stops immediately. The seller and the highest bidder are notified.'
        }
        confirmLabel={target === 'active' ? 'Start auction' : 'Close auction'}
        tone={target === 'closed' ? 'danger' : 'default'}
        loading={setStatus.isPending}
        onCancel={() => setSelected(null)}
        onConfirm={() =>
          selected &&
          setStatus.mutate(
            { id: selected.id, status: target },
            {
              onSuccess: () => toast.success(target === 'active' ? 'Auction started' : 'Auction closed'),
              onError: (e) => toast.error(e.message),
              onSettled: () => setSelected(null),
            },
          )
        }
      />
    </Card>
  )
}

export function AuctionControl() {
  return (
    <div className="grid gap-6 xl:grid-cols-2">
      <ProductList status="active" target="closed" title="Live auctions" description="Close an auction before its timer ends." />
      <ProductList status="draft" target="active" title="Drafts" description="Start an auction directly, without a request." />
    </div>
  )
}
