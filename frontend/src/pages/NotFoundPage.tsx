import { Compass } from 'lucide-react'
import { Link } from 'react-router'
import { buttonClasses } from '@/components/ui/buttonStyles'
import { EmptyState } from '@/components/ui/States'

export function NotFoundPage() {
  return (
    <EmptyState
      icon={Compass}
      title="Page not found"
      description="The page you’re looking for doesn’t exist or has moved."
      action={<Link to="/" className={buttonClasses({ variant: 'primary' })}>Back to marketplace</Link>}
      className="my-10"
    />
  )
}
