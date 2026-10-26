import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Link, useLocation, useNavigate } from 'react-router'
import { toast } from 'sonner'
import { isApiError } from '@/api/client'
import { usersApi } from '@/api/endpoints'
import { useAuth } from '@/auth/AuthContext'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { FormField, Input } from '@/components/ui/Field'
import { registerSchema } from '@/lib/schemas'
import { AuthShell } from './AuthShell'

type Values = { username: string; email: string; password: string; confirm: string }

export function RegisterPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<Values>({ resolver: zodResolver(registerSchema) })

  const submit = handleSubmit(async ({ username, email, password }) => {
    try {
      await usersApi.register({ username, email, password })
    } catch (error) {
      let mapped = false
      if (isApiError(error)) {
        for (const fe of error.fieldErrors) {
          if (fe.field === 'username' || fe.field === 'email' || fe.field === 'password') {
            setError(fe.field, { message: fe.message })
            mapped = true
          }
        }
      }
      if (!mapped) setError('root', { message: error instanceof Error ? error.message : 'Registration failed.' })
      return
    }
    try {
      await login(username, password)
      toast.success(`Welcome, ${username}!`)
    } catch {
      navigate('/login', { state: { notice: 'Account created. Please sign in.' } })
    }
  })

  return (
    <AuthShell
      title="Create your account"
      description="Join to bid on live auctions and list your own items."
      footer={
        <>
          Already have an account?{' '}
          <Link to={`/login${location.search}`} className="font-medium text-brand-700 hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={submit} noValidate className="space-y-5">
        {errors.root?.message && <Alert tone="error">{errors.root.message}</Alert>}
        <FormField label="Username" error={errors.username?.message} hint="3–50 characters. Shown to other members.">
          {(field) => <Input {...field} {...register('username')} autoComplete="username" autoFocus />}
        </FormField>
        <FormField label="Email" error={errors.email?.message}>
          {(field) => <Input {...field} {...register('email')} type="email" autoComplete="email" />}
        </FormField>
        <FormField label="Password" error={errors.password?.message} hint="At least 8 characters.">
          {(field) => <Input {...field} {...register('password')} type="password" autoComplete="new-password" />}
        </FormField>
        <FormField label="Confirm password" error={errors.confirm?.message}>
          {(field) => <Input {...field} {...register('confirm')} type="password" autoComplete="new-password" />}
        </FormField>
        <Button type="submit" size="lg" className="w-full" loading={isSubmitting}>
          Create account
        </Button>
      </form>
    </AuthShell>
  )
}
