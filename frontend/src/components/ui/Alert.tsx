import { AlertTriangle, CheckCircle2, Info, XCircle } from 'lucide-react'
import type { ReactNode } from 'react'
import { cn } from '@/lib/cn'

const tones = {
  info: { icon: Info, className: 'bg-sky-50 text-sky-900 ring-sky-200', iconClass: 'text-sky-600' },
  success: { icon: CheckCircle2, className: 'bg-brand-50 text-brand-900 ring-brand-200', iconClass: 'text-brand-600' },
  warning: { icon: AlertTriangle, className: 'bg-amber-50 text-amber-900 ring-amber-200', iconClass: 'text-amber-600' },
  error: { icon: XCircle, className: 'bg-rose-50 text-rose-900 ring-rose-200', iconClass: 'text-rose-600' },
}

export function Alert({
  tone = 'info',
  title,
  children,
  className,
}: {
  tone?: keyof typeof tones
  title?: string
  children?: ReactNode
  className?: string
}) {
  const { icon: Icon, className: toneClass, iconClass } = tones[tone]
  return (
    <div
      role={tone === 'error' ? 'alert' : 'status'}
      className={cn('flex gap-3 rounded-xl p-3.5 text-sm ring-1 ring-inset', toneClass, className)}
    >
      <Icon className={cn('mt-0.5 size-4 shrink-0', iconClass)} aria-hidden />
      <div className="min-w-0 space-y-1">
        {title && <p className="font-medium">{title}</p>}
        {children && <div className="opacity-90">{children}</div>}
      </div>
    </div>
  )
}
