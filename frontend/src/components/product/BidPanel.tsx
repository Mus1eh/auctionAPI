import { zodResolver } from '@hookform/resolvers/zod'
import { Gavel, Lock } from 'lucide-react'
import { useMemo } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useLocation } from 'react-router'
import { toast } from 'sonner'
import { usePlaceBid } from '@/api/queries'
import type { Product } from '@/api/types'
import { useAuth } from '@/auth/AuthContext'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { buttonClasses } from '@/components/ui/buttonStyles'
import { FormField, Input } from '@/components/ui/Field'
import { useNow } from '@/hooks/useNow'
import { cn } from '@/lib/cn'
import { formatPrice } from '@/lib/format'
import { suggestedBids } from '@/lib/products'
import { bidSchema } from '@/lib/schemas'

function BidForm({ product }: { product: Product }) {
  const placeBid = usePlaceBid(product.id)
  const schema = useMemo(() => bidSchema(product.current_price), [product.current_price])
  const {
    register,
    handleSubmit,
    setValue,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<{ amount: number }>({ resolver: zodResolver(schema) })

  const submit = handleSubmit(async ({ amount }) => {
    try {
      await placeBid.mutateAsync(amount)
      toast.success(`Bid of ${formatPrice(amount)} placed`, { description: 'You are now the highest bidder.' })
      reset({ amount: undefined as unknown as number })
    } catch (error) {
      setError('amount', { message: error instanceof Error ? error.message : 'Could not place bid.' })
    }
  })

  return (
    <form onSubmit={submit} noValidate className="space-y-3">
      <FormField label="Your bid" error={errors.amount?.message} hint={`Enter more than ${formatPrice(product.current_price)}`}>
        {(field) => (
          <Input
            {...field}
            {...register('amount', { valueAsNumber: true })}
            type="number"
            inputMode="numeric"
            min={product.current_price + 1}
            step={1}
            placeholder={String(product.current_price + 1)}
            className="h-12 text-base tabular"
          />
        )}
      </FormField>
      <div className="flex flex-wrap gap-2" aria-label="Quick bid amounts">
        {suggestedBids(product.current_price).map((amount) => (
          <button
            key={amount}
            type="button"
            onClick={() => setValue('amount', amount, { shouldValidate: true })}
            className="rounded-full bg-stone-100 px-3 py-1 text-xs font-medium text-stone-700 tabular hover:bg-stone-200"
          >
            {formatPrice(amount)}
          </button>
        ))}
      </div>
      <Button type="submit" variant="brand" size="lg" className="w-full" loading={isSubmitting}>
        <Gavel className="size-4" aria-hidden /> Place bid
      </Button>
    </form>
  )
}

export function BidPanel({ product, isOwner, bidCount }: { product: Product; isOwner: boolean; bidCount: number | null }) {
  const { status } = useAuth()
  const location = useLocation()
  const now = useNow(1000, product.status === 'active')
  const endsAt = product.auction_ends_at ? new Date(product.auction_ends_at).getTime() : null
  const biddingOpen = product.status === 'active' && endsAt !== null && endsAt > now
  const raised = product.current_price > product.start_price

  let body
  if (product.status === 'active' && !biddingOpen) {
    body = <Alert tone="info">The clock has run out. This auction will close automatically in a moment.</Alert>
  } else if (!biddingOpen) {
    body = null
  } else if (status !== 'authenticated') {
    body = (
      <Link
        to={`/login?next=${encodeURIComponent(location.pathname)}`}
        className={buttonClasses({ variant: 'primary', size: 'lg', className: 'w-full' })}
      >
        <Lock className="size-4" aria-hidden /> Sign in to bid
      </Link>
    )
  } else if (isOwner) {
    body = <Alert tone="info">This is your listing, so you can’t bid on it.</Alert>
  } else {
    body = <BidForm product={product} />
  }

  return (
    <div className="space-y-5">
      <div>
        <p className="text-sm text-stone-500">
          {product.status === 'sold' ? 'Sold for' : raised ? 'Current bid' : 'Starting price'}
        </p>
        <p className={cn('mt-1 text-4xl font-semibold tracking-tight tabular', product.status === 'sold' ? 'text-violet-700' : 'text-stone-900')}>
          {formatPrice(product.current_price)}
        </p>
        <p className="mt-1 text-sm text-stone-500">
          {bidCount === null ? null : bidCount === 0 ? 'No bids yet' : `${bidCount}${bidCount >= 10 ? '+' : ''} ${bidCount === 1 ? 'bid' : 'bids'}`}
          {raised && ` · started at ${formatPrice(product.start_price)}`}
        </p>
      </div>
      {body}
    </div>
  )
}
