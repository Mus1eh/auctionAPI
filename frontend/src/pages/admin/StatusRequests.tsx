import { useQueries } from '@tanstack/react-query'
import { Check, Inbox, X } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router'
import { toast } from 'sonner'
import { productsApi } from '@/api/endpoints'
import { queryKeys, usePendingRequests, useReviewRequest } from '@/api/queries'
import type { StatusRequest } from '@/api/types'
import { StatusBadge } from '@/components/product/StatusBadge'
import { Button } from '@/components/ui/Button'
import { Card, CardHeader } from '@/components/ui/Card'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { Skeleton } from '@/components/ui/Skeleton'
import { EmptyState, ErrorState } from '@/components/ui/States'
import { formatDateTime, formatRelative } from '@/lib/format'

export function StatusRequests() {
  const { data, isPending, isError, error, refetch } = usePendingRequests()
  const review = useReviewRequest()
  const [pendingAction, setPendingAction] = useState<{ request: StatusRequest; approve: boolean } | null>(null)

  const productIds = [...new Set((data ?? []).map((r) => r.product_id))]
  const products = useQueries({
    queries: productIds.map((id) => ({ queryKey: queryKeys.product(id), queryFn: () => productsApi.get(id) })),
  })
  const productName = (id: number) => products[productIds.indexOf(id)]?.data?.name

  const confirm = () => {
    if (!pendingAction) return
    const { request, approve } = pendingAction
    review.mutate(
      { id: request.id, approve },
      {
        onSuccess: () => toast.success(approve ? `Request #${request.id} approved. The auction is now live.` : `Request #${request.id} rejected`),
        onError: (e) => toast.error(e.message),
        onSettled: () => setPendingAction(null),
      },
    )
  }

  return (
    <Card>
      <CardHeader title="Go-live requests" description="Approving a request starts a one-hour auction immediately. Oldest requests first." />
      {isPending ? (
        <div className="space-y-3 p-5">
          {Array.from({ length: 3 }, (_, i) => (
            <Skeleton key={i} className="h-14" />
          ))}
        </div>
      ) : isError ? (
        <div className="p-5">
          <ErrorState error={error} onRetry={() => refetch()} />
        </div>
      ) : data.length === 0 ? (
        <div className="p-5">
          <EmptyState icon={Inbox} title="All caught up" description="There are no pending requests." className="border-0" />
        </div>
      ) : (
        <ul className="divide-y divide-stone-100">
          {data.map((request) => (
            <li key={request.id} className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:px-6">
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-stone-900">
                  <Link to={`/products/${request.product_id}`} className="hover:underline">
                    {productName(request.product_id) ?? `Lot #${request.product_id}`}
                  </Link>
                  <span className="ml-2 text-xs font-normal text-stone-500">Request #{request.id}</span>
                </p>
                <p className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-stone-500">
                  <span>User #{request.requested_by} wants to set the status to</span>
                  <StatusBadge status={request.requested_status} />
                  <span title={formatDateTime(request.created_at)}>· {formatRelative(request.created_at)}</span>
                </p>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="secondary" onClick={() => setPendingAction({ request, approve: false })}>
                  <X className="size-4" aria-hidden /> Reject
                </Button>
                <Button size="sm" variant="brand" onClick={() => setPendingAction({ request, approve: true })}>
                  <Check className="size-4" aria-hidden /> Approve
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}
      <ConfirmDialog
        open={pendingAction !== null}
        title={pendingAction?.approve ? 'Approve and start the auction?' : 'Reject this request?'}
        description={
          pendingAction?.approve
            ? 'The listing goes live now and accepts bids for one hour.'
            : 'The listing stays a draft. The seller can submit a new request.'
        }
        confirmLabel={pendingAction?.approve ? 'Approve' : 'Reject'}
        tone={pendingAction?.approve ? 'default' : 'danger'}
        loading={review.isPending}
        onConfirm={confirm}
        onCancel={() => setPendingAction(null)}
      />
    </Card>
  )
}
