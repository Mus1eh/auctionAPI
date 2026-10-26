import type { ReactNode } from 'react'

export function PageHeader({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: ReactNode; action?: ReactNode }) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        {eyebrow && <p className="text-sm font-medium text-brand-700">{eyebrow}</p>}
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-stone-900 sm:text-3xl">{title}</h1>
        {description && <p className="mt-2 max-w-2xl text-stone-600">{description}</p>}
      </div>
      {action && <div className="flex shrink-0 gap-2">{action}</div>}
    </div>
  )
}
