import { useSearchParams } from 'react-router'
import { usePendingRequests } from '@/api/queries'
import { PageHeader } from '@/components/layout/PageHeader'
import { cn } from '@/lib/cn'
import { AdminOverview } from './AdminOverview'
import { AuctionControl } from './AuctionControl'
import { StatusRequests } from './StatusRequests'
import { UserManagement } from './UserManagement'

const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'requests', label: 'Requests' },
  { id: 'auctions', label: 'Auctions' },
  { id: 'users', label: 'Users' },
] as const

type TabId = (typeof TABS)[number]['id']

export function AdminPage() {
  const [params, setParams] = useSearchParams()
  const tabParam = params.get('tab')
  const tab: TabId = TABS.some((t) => t.id === tabParam) ? (tabParam as TabId) : 'overview'
  const pending = usePendingRequests()
  const go = (id: string) => setParams(id === 'overview' ? {} : { tab: id })

  return (
    <div className="space-y-8">
      <PageHeader eyebrow="Administration" title="Admin console" description="Review go-live requests, control auctions and manage users." />
      <div role="tablist" aria-label="Admin sections" className="-mx-1 flex gap-1 overflow-x-auto border-b border-stone-200 px-1">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            type="button"
            aria-selected={tab === t.id}
            onClick={() => go(t.id)}
            className={cn(
              '-mb-px inline-flex shrink-0 items-center gap-2 border-b-2 px-3 py-2.5 text-sm font-medium transition-colors',
              tab === t.id ? 'border-stone-900 text-stone-900' : 'border-transparent text-stone-500 hover:text-stone-800',
            )}
          >
            {t.label}
            {t.id === 'requests' && pending.data && pending.data.length > 0 && (
              <span className="rounded-full bg-amber-100 px-1.5 text-xs font-semibold text-amber-800 tabular">{pending.data.length}</span>
            )}
          </button>
        ))}
      </div>
      <div role="tabpanel">
        {tab === 'overview' && <AdminOverview onNavigate={go} />}
        {tab === 'requests' && <StatusRequests />}
        {tab === 'auctions' && <AuctionControl />}
        {tab === 'users' && <UserManagement />}
      </div>
    </div>
  )
}
