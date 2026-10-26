import { Loader2, RefreshCw, ShieldX, type LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { cn } from '@/lib/cn'
import { Button } from './Button'
import { buttonClasses } from './buttonStyles'

export function Spinner({ className, label = 'Loading' }: { className?: string; label?: string }) {
  return (
    <span role="status" className="inline-flex items-center">
      <Loader2 className={cn('size-5 animate-spin text-stone-400', className)} aria-hidden />
      <span className="sr-only">{label}</span>
    </span>
  )
}

export function PageLoader() {
  return (
    <div className="flex min-h-[50vh] items-center justify-center">
      <Spinner className="size-6" />
    </div>
  )
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon: LucideIcon
  title: string
  description?: ReactNode
  action?: ReactNode
  className?: string
}) {
  return (
    <div className={cn('flex flex-col items-center rounded-2xl border border-dashed border-stone-300 bg-white/60 px-6 py-14 text-center', className)}>
      <div className="flex size-12 items-center justify-center rounded-full bg-stone-100 text-stone-500">
        <Icon className="size-6" aria-hidden />
      </div>
      <h3 className="mt-4 text-base font-semibold text-stone-900">{title}</h3>
      {description && <p className="mt-1 max-w-sm text-sm text-stone-500">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}

export function ErrorState({
  title = 'Something went wrong',
  error,
  onRetry,
  className,
}: {
  title?: string
  error: unknown
  onRetry?: () => void
  className?: string
}) {
  const message = error instanceof Error ? error.message : 'An unexpected error occurred.'
  return (
    <div role="alert" className={cn('flex flex-col items-center rounded-2xl border border-rose-200 bg-rose-50/60 px-6 py-12 text-center', className)}>
      <h3 className="text-base font-semibold text-rose-900">{title}</h3>
      <p className="mt-1 max-w-md text-sm text-rose-800/80">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" className="mt-4" onClick={onRetry}>
          <RefreshCw className="size-4" aria-hidden /> Try again
        </Button>
      )}
    </div>
  )
}

export function AccessDenied({ message = 'Your account does not have permission to view this page.' }: { message?: string }) {
  return (
    <EmptyState
      icon={ShieldX}
      title="Access denied"
      description={message}
      action={
        <Link to="/" className={buttonClasses({ variant: 'secondary' })}>
          Back to marketplace
        </Link>
      }
      className="my-10"
    />
  )
}
