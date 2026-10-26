import { ChevronLeft, ChevronRight, Gavel } from 'lucide-react'
import { BIDS_PAGE_SIZE } from '@/api/endpoints'
import { useBids } from '@/api/queries'
import { Button } from '@/components/ui/Button'
import { Card, CardHeader } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import { ErrorState } from '@/components/ui/States'
import { cn } from '@/lib/cn'
import { formatDateTime, formatPrice, formatRelative } from '@/lib/format'

interface BidHistoryProps {
  productId: number
  live: boolean
  page: number
  onPageChange: (page: number) => void
  /** Current user's id when it can be inferred, to highlight their bids. */
  myUserId: number | null
}

export function BidHistory({ productId, live, page, onPageChange, myUserId }: BidHistoryProps) {
  const { data, isPending, isError, error, refetch, isPlaceholderData } = useBids(productId, page, live)
  const hasNext = (data?.length ?? 0) === BIDS_PAGE_SIZE

  return (
    <Card>
      <CardHeader
        title="Bid history"
        description={live ? 'Updates automatically every few seconds.' : 'Most recent bids first.'}
        action={live ? <span className="inline-flex items-center gap-1.5 text-xs font-medium text-brand-700"><span className="size-1.5 animate-pulse rounded-full bg-brand-500" />Live</span> : undefined}
      />
      {isPending ? (
        <div className="space-y-3 p-5 sm:p-6">
          {Array.from({ length: 4 }, (_, i) => (
            <Skeleton key={i} className="h-10" />
          ))}
        </div>
      ) : isError ? (
        <div className="p-5">
          <ErrorState title="Could not load bids" error={error} onRetry={() => refetch()} />
        </div>
      ) : data.length === 0 ? (
        <div className="flex flex-col items-center px-6 py-12 text-center">
          <Gavel className="size-6 text-stone-300" aria-hidden />
          <p className="mt-3 text-sm font-medium text-stone-700">{page === 1 ? 'No bids yet' : 'No more bids'}</p>
          {page === 1 && <p className="mt-1 text-sm text-stone-500">{live ? 'Be the first to bid on this lot.' : 'Nobody bid on this lot.'}</p>}
        </div>
      ) : (
        <div className={cn('overflow-x-auto transition-opacity', isPlaceholderData && 'opacity-60')}>
          <table className="w-full text-left text-sm">
            <thead className="text-xs text-stone-500">
              <tr className="border-b border-stone-100">
                <th scope="col" className="px-5 py-2.5 font-medium sm:px-6">Bidder</th>
                <th scope="col" className="px-5 py-2.5 text-right font-medium sm:px-6">Amount</th>
                <th scope="col" className="hidden px-5 py-2.5 text-right font-medium sm:table-cell sm:px-6">Placed</th>
              </tr>
            </thead>
            <tbody>
              {data.map((bid, index) => {
                const leading = page === 1 && index === 0
                const mine = myUserId !== null && bid.user_id === myUserId
                return (
                  <tr key={bid.id} className="border-b border-stone-100 last:border-0">
                    <td className="px-5 py-3 sm:px-6">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-stone-800">Bidder #{bid.user_id}</span>
                        {mine && <span className="rounded bg-sky-50 px-1.5 py-0.5 text-[11px] font-medium text-sky-700 ring-1 ring-sky-200 ring-inset">You</span>}
                        {leading && <span className="rounded bg-brand-50 px-1.5 py-0.5 text-[11px] font-medium text-brand-700 ring-1 ring-brand-200 ring-inset">Highest</span>}
                      </div>
                      <p className="text-xs text-stone-500 sm:hidden">{formatRelative(bid.created_at)}</p>
                    </td>
                    <td className={cn('px-5 py-3 text-right font-semibold tabular sm:px-6', leading ? 'text-stone-900' : 'text-stone-600')}>
                      {formatPrice(bid.amount)}
                    </td>
                    <td className="hidden px-5 py-3 text-right text-stone-500 sm:table-cell sm:px-6" title={formatDateTime(bid.created_at)}>
                      {formatRelative(bid.created_at)}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
      {(page > 1 || hasNext) && (
        <div className="flex items-center justify-between border-t border-stone-100 px-5 py-3 sm:px-6">
          <Button variant="secondary" size="sm" disabled={page === 1} onClick={() => onPageChange(page - 1)}>
            <ChevronLeft className="size-4" aria-hidden /> Newer
          </Button>
          <span className="text-xs text-stone-500">Page {page}</span>
          <Button variant="secondary" size="sm" disabled={!hasNext || isPlaceholderData} onClick={() => onPageChange(page + 1)}>
            Older <ChevronRight className="size-4" aria-hidden />
          </Button>
        </div>
      )}
    </Card>
  )
}
