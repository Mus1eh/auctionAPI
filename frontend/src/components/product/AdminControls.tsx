import { Play, ShieldCheck, Square } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { useSetProductStatus } from '@/api/queries'
import type { Product } from '@/api/types'
import { Button } from '@/components/ui/Button'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'

/** Admin-only lifecycle controls (POST /admin/products/{id}/status/{active|closed}). */
export function AdminControls({ product }: { product: Product }) {
  const setStatus = useSetProductStatus()
  const [open, setOpen] = useState(false)
  const target = product.status === 'draft' ? 'active' : product.status === 'active' ? 'closed' : null

  if (!target) return null

  return (
    <div className="rounded-xl border border-dashed border-stone-300 p-4">
      <p className="flex items-center gap-1.5 text-xs font-semibold tracking-wide text-stone-500 uppercase">
        <ShieldCheck className="size-3.5" aria-hidden /> Admin
      </p>
      <Button variant="secondary" size="sm" className="mt-3 w-full" onClick={() => setOpen(true)}>
        {target === 'active' ? <Play className="size-4" aria-hidden /> : <Square className="size-4" aria-hidden />}
        {target === 'active' ? 'Start auction now' : 'Close auction now'}
      </Button>
      <ConfirmDialog
        open={open}
        title={target === 'active' ? 'Start this auction?' : 'Close this auction early?'}
        description={
          target === 'active'
            ? 'Bidding opens immediately and runs for one hour.'
            : 'Bidding stops immediately. The seller and the highest bidder are notified by email.'
        }
        confirmLabel={target === 'active' ? 'Start auction' : 'Close auction'}
        tone={target === 'closed' ? 'danger' : 'default'}
        loading={setStatus.isPending}
        onCancel={() => setOpen(false)}
        onConfirm={async () => {
          try {
            await setStatus.mutateAsync({ id: product.id, status: target })
            toast.success(target === 'active' ? 'Auction started' : 'Auction closed')
          } catch (error) {
            toast.error(error instanceof Error ? error.message : 'Could not change the auction status.')
          }
          setOpen(false)
        }}
      />
    </div>
  )
}
