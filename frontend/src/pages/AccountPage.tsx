import { zodResolver } from '@hookform/resolvers/zod'
import { LogOut, ShieldCheck } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router'
import { toast } from 'sonner'
import { authApi } from '@/api/endpoints'
import { useAuth } from '@/auth/AuthContext'
import { PageHeader } from '@/components/layout/PageHeader'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Card, CardHeader } from '@/components/ui/Card'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { FormField, Input } from '@/components/ui/Field'
import { changePasswordSchema } from '@/lib/schemas'

const ROLE_LABELS = { user: 'Member', admin: 'Admin', superadmin: 'Super admin' }

function ChangePasswordForm() {
  const { endSession } = useAuth()
  const navigate = useNavigate()
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<{ current: string; password: string; confirm: string }>({ resolver: zodResolver(changePasswordSchema) })

  const submit = handleSubmit(async ({ current, password }) => {
    try {
      await authApi.changePassword(current, password)
    } catch (error) {
      setError('root', { message: error instanceof Error ? error.message : 'Could not change password.' })
      return
    }
    // The backend revokes every refresh token on password change, so this session is over too.
    endSession()
    navigate('/login', { replace: true, state: { notice: 'Password changed. Sign in again with your new password.' } })
  })

  return (
    <form onSubmit={submit} noValidate className="space-y-5 p-5 sm:p-6">
      {errors.root?.message && <Alert tone="error">{errors.root.message}</Alert>}
      <FormField label="Current password" error={errors.current?.message}>
        {(field) => <Input {...field} {...register('current')} type="password" autoComplete="current-password" />}
      </FormField>
      <div className="grid gap-5 sm:grid-cols-2">
        <FormField label="New password" error={errors.password?.message} hint="At least 8 characters.">
          {(field) => <Input {...field} {...register('password')} type="password" autoComplete="new-password" />}
        </FormField>
        <FormField label="Confirm new password" error={errors.confirm?.message}>
          {(field) => <Input {...field} {...register('confirm')} type="password" autoComplete="new-password" />}
        </FormField>
      </div>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs text-stone-500">You’ll be signed out on every device, including this one.</p>
        <Button type="submit" loading={isSubmitting}>
          Update password
        </Button>
      </div>
    </form>
  )
}

function SessionsCard() {
  const { endSession } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)

  const signOutEverywhere = async () => {
    setLoading(true)
    try {
      const result = await authApi.logoutAll()
      toast.success(`Signed out of ${result.count} ${result.count === 1 ? 'session' : 'sessions'}`)
      endSession()
      navigate('/login', { replace: true })
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Could not sign out of all sessions.')
      setLoading(false)
      setOpen(false)
    }
  }

  return (
    <Card>
      <CardHeader title="Sessions" description="Signed in on a shared or lost device? End every session at once." />
      <div className="p-5 sm:p-6">
        <Button variant="secondary" onClick={() => setOpen(true)}>
          <LogOut className="size-4" aria-hidden /> Sign out of all devices
        </Button>
      </div>
      <ConfirmDialog
        open={open}
        title="Sign out everywhere?"
        description="Every active session, including this one, will be ended."
        confirmLabel="Sign out everywhere"
        tone="danger"
        loading={loading}
        onConfirm={signOutEverywhere}
        onCancel={() => setOpen(false)}
      />
    </Card>
  )
}

export function AccountPage() {
  const { username, role } = useAuth()

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <PageHeader eyebrow="Account" title="Account & security" />

      <Card className="flex items-center gap-4 p-5 sm:p-6">
        <span className="flex size-14 shrink-0 items-center justify-center rounded-full bg-stone-900 text-xl font-semibold text-white uppercase">
          {username?.[0] ?? '?'}
        </span>
        <div className="min-w-0">
          <p className="truncate text-lg font-semibold text-stone-900">{username}</p>
          <p className="mt-0.5 inline-flex items-center gap-1.5 text-sm text-stone-600">
            {role !== 'user' && <ShieldCheck className="size-4 text-brand-600" aria-hidden />}
            {role ? ROLE_LABELS[role] : ''}
          </p>
        </div>
      </Card>

      <Card>
        <CardHeader title="Change password" />
        <ChangePasswordForm />
      </Card>

      <SessionsCard />
    </div>
  )
}
