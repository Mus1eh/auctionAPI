import { zodResolver } from '@hookform/resolvers/zod'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate, useSearchParams } from 'react-router'
import { authApi } from '@/api/endpoints'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { buttonClasses } from '@/components/ui/buttonStyles'
import { FormField, Input } from '@/components/ui/Field'
import { Spinner } from '@/components/ui/States'
import { resetPasswordSchema } from '@/lib/schemas'
import { AuthShell } from './AuthShell'

function TokenEntry({ onSubmit }: { onSubmit: (token: string) => void }) {
  const [value, setValue] = useState('')
  return (
    <form
      noValidate
      className="space-y-5"
      onSubmit={(e) => {
        e.preventDefault()
        if (value.trim()) onSubmit(value.trim())
      }}
    >
      <FormField label="Reset token" hint="Paste the token from your password reset email.">
        {(field) => <Input {...field} value={value} onChange={(e) => setValue(e.target.value)} autoComplete="off" autoFocus />}
      </FormField>
      <Button type="submit" size="lg" className="w-full" disabled={!value.trim()}>
        Continue
      </Button>
    </form>
  )
}

function NewPasswordForm({ token }: { token: string }) {
  const navigate = useNavigate()
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<{ password: string; confirm: string }>({ resolver: zodResolver(resetPasswordSchema) })

  const submit = handleSubmit(async ({ password }) => {
    try {
      await authApi.resetPassword(token, password)
      navigate('/login', { replace: true, state: { notice: 'Password updated. Sign in with your new password.' } })
    } catch (error) {
      setError('root', { message: error instanceof Error ? error.message : 'Could not reset password.' })
    }
  })

  return (
    <form onSubmit={submit} noValidate className="space-y-5">
      {errors.root?.message && <Alert tone="error">{errors.root.message}</Alert>}
      <FormField label="New password" error={errors.password?.message} hint="At least 8 characters. Must differ from your old password.">
        {(field) => <Input {...field} {...register('password')} type="password" autoComplete="new-password" autoFocus />}
      </FormField>
      <FormField label="Confirm new password" error={errors.confirm?.message}>
        {(field) => <Input {...field} {...register('confirm')} type="password" autoComplete="new-password" />}
      </FormField>
      <Button type="submit" size="lg" className="w-full" loading={isSubmitting}>
        Set new password
      </Button>
      <p className="text-center text-xs text-stone-500">You’ll be signed out on all devices.</p>
    </form>
  )
}

export function ResetPasswordPage() {
  const [params, setParams] = useSearchParams()
  const token = params.get('token')
  const verify = useQuery({
    queryKey: ['reset-token', token],
    queryFn: () => authApi.verifyResetToken(token!),
    enabled: Boolean(token),
    retry: false,
    staleTime: Infinity,
  })

  let body
  if (!token) {
    body = <TokenEntry onSubmit={(t) => setParams({ token: t }, { replace: true })} />
  } else if (verify.isPending) {
    body = (
      <div className="flex items-center justify-center gap-2 py-6 text-sm text-stone-500">
        <Spinner /> Checking your reset link…
      </div>
    )
  } else if (verify.isError) {
    body = (
      <div className="space-y-5">
        <Alert tone="error" title="This reset link can’t be used">
          {verify.error.message}
        </Alert>
        <Link to="/forgot-password" className={buttonClasses({ variant: 'primary', className: 'w-full' })}>
          Request a new link
        </Link>
      </div>
    )
  } else {
    body = <NewPasswordForm token={token} />
  }

  return (
    <AuthShell
      title="Choose a new password"
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
