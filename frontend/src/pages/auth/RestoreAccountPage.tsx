import { CheckCircle2 } from 'lucide-react'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { usersApi } from '@/api/endpoints'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { buttonClasses } from '@/components/ui/buttonStyles'
import { AuthShell } from './AuthShell'

export function RestoreAccountPage() {
  const [params] = useSearchParams()
  const token = params.get('token')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [doneMessage, setDoneMessage] = useState<string | null>(null)

  async function restore() {
    if (!token) return
    setLoading(true)
    setError(null)
    try {
      const result = await usersApi.restore(token)
      setDoneMessage(result.message)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not restore your account.')
    } finally {
      setLoading(false)
    }
  }

  let body
  if (!token) {
    body = (
      <div className="space-y-5">
        <Alert tone="error" title="Missing restore link">
          Open the link from your restore email, or request a new one.
        </Alert>
        <Link to="/restore-request" className={buttonClasses({ variant: 'primary', className: 'w-full' })}>
          Request a restore link
        </Link>
      </div>
    )
  } else if (doneMessage) {
    body = (
      <div className="flex flex-col items-center text-center">
        <div className="flex size-12 items-center justify-center rounded-full bg-brand-50 text-brand-600">
          <CheckCircle2 className="size-6" aria-hidden />
        </div>
        <p className="mt-4 font-medium text-stone-900">Account restored</p>
        <p className="mt-1 text-sm text-stone-600">{doneMessage}</p>
        <Link to="/login" className={buttonClasses({ variant: 'primary', className: 'mt-6 w-full' })}>
          Sign in
        </Link>
      </div>
    )
  } else {
    body = (
      <div className="space-y-5">
        {error && (
          <Alert tone="error" title="This restore link can’t be used">
            {error}
          </Alert>
        )}
        <Button size="lg" className="w-full" loading={loading} onClick={restore}>
          Restore my account
        </Button>
        {error && (
          <Link to="/restore-request" className={buttonClasses({ variant: 'secondary', className: 'w-full' })}>
            Request a new link
          </Link>
        )}
      </div>
    )
  }

  return (
    <AuthShell
      title="Restore your account"
      description={token && !doneMessage ? 'Confirm to reactivate your account.' : undefined}
      footer={
        <Link to="/login" className="font-medium text-brand-700 hover:underline">
          Back to sign in
        </Link>
      }
    >
      {body}
    </AuthShell>
  )
}
