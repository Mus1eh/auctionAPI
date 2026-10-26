import { zodResolver } from '@hookform/resolvers/zod'
import { MailCheck } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router'
import { authApi } from '@/api/endpoints'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { buttonClasses } from '@/components/ui/buttonStyles'
import { FormField, Input } from '@/components/ui/Field'
import { forgotPasswordSchema } from '@/lib/schemas'
import { AuthShell } from './AuthShell'

export function ForgotPasswordPage() {
  const [sentMessage, setSentMessage] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<{ email: string }>({ resolver: zodResolver(forgotPasswordSchema) })

  const submit = handleSubmit(async ({ email }) => {
    try {
      const result = await authApi.forgotPassword(email)
      setSentMessage(result.message)
    } catch (error) {
      setError('root', { message: error instanceof Error ? error.message : 'Request failed.' })
    }
  })

  return (
    <AuthShell
      title="Reset your password"
      description="Enter your account email and we’ll send you a reset link."
      footer={
        <Link to="/login" className="font-medium text-brand-700 hover:underline">
          Back to sign in
        </Link>
      }
    >
      {sentMessage ? (
        <div className="flex flex-col items-center text-center">
          <div className="flex size-12 items-center justify-center rounded-full bg-brand-50 text-brand-600">
            <MailCheck className="size-6" aria-hidden />
          </div>
          <p className="mt-4 font-medium text-stone-900">Check your inbox</p>
          <p className="mt-1 text-sm text-stone-600">{sentMessage}. The link expires after a short time.</p>
          <Link to="/reset-password" className={buttonClasses({ variant: 'secondary', className: 'mt-6' })}>
            I have a reset token
          </Link>
        </div>
      ) : (
        <form onSubmit={submit} noValidate className="space-y-5">
          {errors.root?.message && <Alert tone="error">{errors.root.message}</Alert>}
          <FormField label="Email" error={errors.email?.message}>
            {(field) => <Input {...field} {...register('email')} type="email" autoComplete="email" autoFocus />}
          </FormField>
          <Button type="submit" size="lg" className="w-full" loading={isSubmitting}>
            Send reset link
          </Button>
        </form>
      )}
    </AuthShell>
  )
}
