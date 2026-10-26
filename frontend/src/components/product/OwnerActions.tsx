import { CheckCircle2, Pencil, Rocket, Trash2, XCircle } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { toast } from 'sonner'
import { isApiError } from '@/api/client'
import { useDecideBid, useDeleteProduct, useRequestGoLive } from '@/api/queries'
import type { Bid, BidDecision, Product } from '@/api/types'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { buttonClasses } from '@/components/ui/buttonStyles'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { formatPrice } from '@/lib/format'

function GoLiveRequest({ product }: { product: Product }) {
  const request = useRequestGoLive()
  const [submittedId, setSubmittedId] = useState<number | null>(null)
  const alreadyPending = isApiError(request.error, 409)

  if (submittedId !== null || alreadyPending) {
    return (
      <Alert tone="success" title="Awaiting admin review">
        {submittedId !== null ? `Request #${submittedId} was sent. ` : 'A go-live request for this listing is already pending. '}
        Once approved, bidding opens for one hour.
      </Alert>
    )
  }

  return (
    <div className="space-y-2">
      <Button
        variant="brand"
        className="w-full"
        loading={request.isPending}
        onClick={() =>
          request.mutate(product.id, {
            onSuccess: (data) => {
              setSubmittedId(data.id)
              toast.success('Go-live request sent', { description: 'An admin will review it shortly.' })
            },
          })
        }
      >
        <Rocket className="size-4" aria-hidden /> Request to go live
      </Button>
      {request.isError && !alreadyPending && <Alert tone="error">{request.error.message}</Alert>}
      <p className="text-xs text-stone-500">An admin approves each listing before its one-hour auction starts.</p>
    </div>
  )
}

function BidDecisionPanel({ product, topBid }: { product: Product; topBid: Bid | undefined }) {
  const decide = useDecideBid(product.id)
  const [pending, setPending] = useState<BidDecision | null>(null)

  if (!topBid) {
    return <Alert tone="info">No bids were placed on this lot, so there is nothing to approve.</Alert>
  }

  // mutateAsync (not per-call callbacks): approving flips the status, which unmounts this panel.
  const confirm = async () => {
    if (!pending) return
    try {
      const result = await decide.mutateAsync(pending)
      toast.success(
        pending === 'approve'
          ? `Sold${result.winning_bidder ? ` to ${result.winning_bidder.username}` : ''} for ${formatPrice(result.current_price)}`
          : 'Highest bid declined',
        { description: 'The bidder will be notified by email.' },
      )
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Could not record your decision.')
    }
    setPending(null)
  }

  return (
    <div className="space-y-3">
      <div className="rounded-xl bg-stone-50 p-3.5 text-sm ring-1 ring-stone-200 ring-inset">
        <p className="text-stone-500">Highest bid</p>
        <p className="mt-0.5 font-semibold text-stone-900 tabular">
          {formatPrice(topBid.amount)} <span className="font-normal text-stone-500">by Bidder #{topBid.user_id}</span>
        </p>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        <Button variant="brand" onClick={() => setPending('approve')}>
          <CheckCircle2 className="size-4" aria-hidden /> Accept & sell
        </Button>
        {product.status === 'closed' && (
          <Button variant="secondary" onClick={() => setPending('reject')}>
            <XCircle className="size-4" aria-hidden /> Decline
          </Button>
        )}
      </div>
      {product.status === 'rejected' && <p className="text-xs text-stone-500">You declined this bid earlier. You can still accept it.</p>}
      <ConfirmDialog
        open={pending !== null}
        title={pending === 'approve' ? 'Accept the highest bid?' : 'Decline the highest bid?'}
        description={
          pending === 'approve'
            ? `The lot will be marked as sold for ${formatPrice(topBid.amount)} and the winning bidder will be emailed. This cannot be undone.`
            : 'The bidder will be emailed that their offer was declined.'
        }
        confirmLabel={pending === 'approve' ? 'Accept & sell' : 'Decline bid'}
        tone={pending === 'reject' ? 'danger' : 'default'}
        loading={decide.isPending}
        onConfirm={confirm}
        onCancel={() => setPending(null)}
      />
    </div>
  )
}

export function ManageListing({ product, isOwner, topBid }: { product: Product; isOwner: boolean; topBid: Bid | undefined }) {
  const navigate = useNavigate()
  const remove = useDeleteProduct()
  const [confirmDelete, setConfirmDelete] = useState(false)

  return (
    <div className="space-y-4">
      {isOwner && product.status === 'draft' && <GoLiveRequest product={product} />}
      {isOwner && (product.status === 'closed' || product.status === 'rejected') && <BidDecisionPanel product={product} topBid={topBid} />}
      <div className="flex gap-2">
        <Link to={`/products/${product.id}/edit`} className={buttonClasses({ variant: 'secondary', className: 'flex-1' })}>
          <Pencil className="size-4" aria-hidden /> Edit
        </Link>
        <Button variant="danger-ghost" className="flex-1" onClick={() => setConfirmDelete(true)}>
          <Trash2 className="size-4" aria-hidden /> Delete
        </Button>
      </div>
      <ConfirmDialog
        open={confirmDelete}
        title={`Delete “${product.name}”?`}
        description="The listing will be permanently removed. This cannot be undone."
        confirmLabel="Delete listing"
        tone="danger"
        loading={remove.isPending}
        onCancel={() => setConfirmDelete(false)}
        onConfirm={async () => {
          try {
            await remove.mutateAsync(product.id)
            toast.success('Listing deleted')
            navigate(isOwner ? '/my-listings' : '/', { replace: true })
          } catch (error) {
            toast.error(error instanceof Error ? error.message : 'Could not delete the listing.')
            setConfirmDelete(false)
          }
        }}
      />
    </div>
  )
}
