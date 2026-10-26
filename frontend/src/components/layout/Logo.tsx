import { Gavel } from 'lucide-react'
import { Link } from 'react-router'
import { APP_NAME } from '@/lib/env'

export function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2 rounded-lg font-semibold tracking-tight text-stone-900">
      <span className="flex size-8 items-center justify-center rounded-lg bg-stone-900 text-white">
        <Gavel className="size-4" aria-hidden />
      </span>
      <span className="text-lg">{APP_NAME}</span>
    </Link>
  )
}
