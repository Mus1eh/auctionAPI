import { AlertTriangle } from 'lucide-react'
import { useEffect, useId, useRef, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { Button } from './Button'

interface ConfirmDialogProps {
  open: boolean
  title: string
  description?: ReactNode
  confirmLabel?: string
  tone?: 'danger' | 'default'
  loading?: boolean
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = 'Confirm',
  tone = 'default',
  loading,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const titleId = useId()
  const descId = useId()
  const panelRef = useRef<HTMLDivElement>(null)
  const cancelRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!open) return
    const previouslyFocused = document.activeElement as HTMLElement | null
    cancelRef.current?.focus()

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !loading) onCancel()
      if (event.key === 'Tab' && panelRef.current) {
        const focusable = panelRef.current.querySelectorAll<HTMLElement>('button:not([disabled])')
        const first = focusable[0]
        const last = focusable[focusable.length - 1]
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault()
          last?.focus()
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault()
          first?.focus()
        }
      }
    }
    document.addEventListener('keydown', onKeyDown)
    const { overflow } = document.body.style
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = overflow
      previouslyFocused?.focus?.()
    }
  }, [open, loading, onCancel])

  if (!open) return null

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-end justify-center p-4 sm:items-center">
      <div className="absolute inset-0 bg-stone-950/40 backdrop-blur-[2px]" onClick={loading ? undefined : onCancel} aria-hidden />
      <div
        ref={panelRef}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? descId : undefined}
        className="relative w-full max-w-md rounded-2xl bg-white p-6 shadow-lift ring-1 ring-stone-200"
      >
        <div className="flex gap-4">
          {tone === 'danger' && (
            <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-rose-100 text-rose-600">
              <AlertTriangle className="size-5" aria-hidden />
            </div>
          )}
          <div className="min-w-0">
            <h2 id={titleId} className="text-base font-semibold text-stone-900">
              {title}
            </h2>
            {description && (
              <div id={descId} className="mt-1.5 text-sm text-stone-600">
                {description}
              </div>
            )}
          </div>
        </div>
        <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button ref={cancelRef} variant="secondary" onClick={onCancel} disabled={loading}>
            Cancel
          </Button>
          <Button variant={tone === 'danger' ? 'danger' : 'primary'} onClick={onConfirm} loading={loading}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>,
    document.body,
  )
}
