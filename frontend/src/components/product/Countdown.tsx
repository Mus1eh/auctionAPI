import { Clock } from 'lucide-react'
import { useNow } from '@/hooks/useNow'
import { cn } from '@/lib/cn'
import { formatCountdown, timeRemaining } from '@/lib/format'

/** Countdown to the real `auction_ends_at` from the API. */
export function Countdown({ endsAt, className, compact }: { endsAt: string; className?: string; compact?: boolean }) {
  const now = useNow(1000)
  const label = formatCountdown(endsAt, now)
  const left = timeRemaining(endsAt, now)
  const urgent = left !== null && left.totalSeconds < 300

  return (
    <span className={cn('inline-flex items-center gap-1.5 tabular', urgent ? 'text-rose-600' : 'text-stone-600', className)}>
      <Clock className={cn(compact ? 'size-3.5' : 'size-4')} aria-hidden />
      {label ? (
        <>
          {!compact && <span className="sr-only">Time left: </span>}
          {compact ? label : `${label} left`}
        </>
      ) : (
        'Closing…'
      )}
    </span>
  )
}
