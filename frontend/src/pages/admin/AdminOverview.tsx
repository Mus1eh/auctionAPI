import { ClipboardList, Gavel, Hourglass, PencilRuler } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useAdminDashboard, usePendingRequests, useProductsByStatus } from '@/api/queries'
import { Card } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import { ErrorState } from '@/components/ui/States'

function Stat({ icon: Icon, label, value, failed, hint, onClick }: { icon: LucideIcon; label: string; value: number | undefined; failed?: boolean; hint: string; onClick: () => void }) {
  return (
    <button type="button" onClick={onClick} className="text-left">
      <Card className="h-full p-5 transition hover:shadow-lift">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-stone-600">{label}</p>
          <Icon className="size-4 text-stone-400" aria-hidden />
        </div>
        {failed ? (
          <p className="mt-2 text-3xl font-semibold text-stone-300" title="Could not load">—</p>
        ) : value === undefined ? <Skeleton className="mt-3 h-8 w-12" /> : <p className="mt-2 text-3xl font-semibold tracking-tight tabular text-stone-900">{value}</p>}
        <p className="mt-1 text-xs text-stone-500">{hint}</p>
      </Card>
    </button>
  )
}

export function AdminOverview({ onNavigate }: { onNavigate: (tab: string) => void }) {
  const dashboard = useAdminDashboard()
  const pending = usePendingRequests()
  const live = useProductsByStatus('active')
  const drafts = useProductsByStatus('draft')
  const closed = useProductsByStatus('closed')

  if (dashboard.isError) return <ErrorState error={dashboard.error} onRetry={() => dashboard.refetch()} />

  return (
    <div className="space-y-6">
      <Card className="p-5 sm:p-6">
        {dashboard.isPending ? (
          <Skeleton className="h-6 w-64" />
        ) : (
          <>
            <p className="text-lg font-semibold text-stone-900">{dashboard.data.message}</p>
            <p className="mt-1 text-sm text-stone-600">
              Signed in as <span className="font-medium text-stone-900">{dashboard.data.username}</span> with the{' '}
              <span className="font-medium text-stone-900">{dashboard.data.role}</span> role.
            </p>
          </>
        )}
      </Card>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Stat icon={ClipboardList} label="Pending requests" value={pending.data?.length} failed={pending.isError} hint="Go-live requests awaiting review" onClick={() => onNavigate('requests')} />
        <Stat icon={Gavel} label="Live auctions" value={live.data?.length} failed={live.isError} hint="Currently accepting bids" onClick={() => onNavigate('auctions')} />
        <Stat icon={PencilRuler} label="Drafts" value={drafts.data?.length} failed={drafts.isError} hint="Not yet live" onClick={() => onNavigate('auctions')} />
        <Stat icon={Hourglass} label="Ended" value={closed.data?.length} failed={closed.isError} hint="Awaiting the seller’s decision" onClick={() => onNavigate('auctions')} />
      </div>
    </div>
  )
}
