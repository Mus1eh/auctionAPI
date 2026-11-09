import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from './Button'

interface PagerProps {
  page: number
  total: number
  pageSize: number
  onPageChange: (page: number) => void
  /** True while the next page is loading, so rapid clicks do not skip pages. */
  busy?: boolean
}

/** Previous/next buttons with "Page X of Y"; renders nothing when everything fits on one page. */
export function Pager({ page, total, pageSize, onPageChange, busy = false }: PagerProps) {
  const pages = Math.max(1, Math.ceil(total / pageSize))
  // Stay visible on a page past the end (e.g. after deleting its last item) so the user can go back.
  if (pages <= 1 && page <= 1) return null

  return (
    <nav aria-label="Pagination" className="flex items-center justify-between gap-3 pt-2">
      <Button variant="secondary" size="sm" disabled={page <= 1 || busy} onClick={() => onPageChange(page - 1)}>
        <ChevronLeft className="size-4" aria-hidden /> Previous
      </Button>
      <span className="text-sm text-stone-500 tabular" aria-live="polite">
        Page {page} of {Math.max(pages, page)}
      </span>
      <Button variant="secondary" size="sm" disabled={page >= pages || busy} onClick={() => onPageChange(page + 1)}>
        Next <ChevronRight className="size-4" aria-hidden />
      </Button>
    </nav>
  )
}
