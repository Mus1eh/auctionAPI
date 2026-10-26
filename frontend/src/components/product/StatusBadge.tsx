import type { ProductStatus } from '@/api/types'
import { cn } from '@/lib/cn'
import { STATUS_META } from './status'

export function StatusBadge({ status, className }: { status: ProductStatus; className?: string }) {
  const meta = STATUS_META[status]
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset',
        meta.className,
        className,
      )}
    >
      <span className="relative flex size-1.5">
        {status === 'active' && <span className={cn('absolute inline-flex size-full animate-ping rounded-full opacity-60', meta.dot)} />}
        <span className={cn('relative inline-flex size-1.5 rounded-full', meta.dot)} />
      </span>
      {meta.label}
    </span>
  )
}
