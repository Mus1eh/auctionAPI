import type { ProductStatus } from '@/api/types'

export const STATUS_META: Record<ProductStatus, { label: string; description: string; className: string; dot: string }> = {
  active: {
    label: 'Live',
    description: 'Accepting bids now',
    className: 'bg-brand-50 text-brand-800 ring-brand-200',
    dot: 'bg-brand-500',
  },
  draft: {
    label: 'Draft',
    description: 'Not yet approved for bidding',
    className: 'bg-amber-50 text-amber-800 ring-amber-200',
    dot: 'bg-amber-500',
  },
  closed: {
    label: 'Ended',
    description: 'Bidding closed, awaiting the seller’s decision',
    className: 'bg-stone-100 text-stone-700 ring-stone-200',
    dot: 'bg-stone-400',
  },
  sold: {
    label: 'Sold',
    description: 'The seller accepted the highest bid',
    className: 'bg-violet-50 text-violet-800 ring-violet-200',
    dot: 'bg-violet-500',
  },
  rejected: {
    label: 'Bid declined',
    description: 'The seller declined the highest bid',
    className: 'bg-rose-50 text-rose-800 ring-rose-200',
    dot: 'bg-rose-500',
  },
}
