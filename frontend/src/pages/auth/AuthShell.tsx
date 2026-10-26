import type { ReactNode } from 'react'
import { Logo } from '@/components/layout/Logo'
import { Card } from '@/components/ui/Card'

export function AuthShell({ title, description, children, footer }: { title: string; description?: ReactNode; children: ReactNode; footer?: ReactNode }) {
  return (
    <div className="mx-auto flex max-w-md flex-col py-4 sm:py-10">
      <div className="mb-8 flex flex-col items-center text-center">
        <div className="sm:hidden">
          <Logo />
        </div>
        <h1 className="mt-4 text-2xl font-semibold tracking-tight text-stone-900 sm:mt-0">{title}</h1>
        {description && <p className="mt-2 text-sm text-stone-600">{description}</p>}
      </div>
      <Card className="p-6 sm:p-8">{children}</Card>
      {footer && <p className="mt-6 text-center text-sm text-stone-600">{footer}</p>}
    </div>
  )
}
