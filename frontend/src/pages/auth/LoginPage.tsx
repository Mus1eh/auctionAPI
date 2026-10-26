import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Link, useLocation } from 'react-router'
import { isApiError } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { FormField, Input } from '@/components/ui/Field'
import { loginSchema } from '@/lib/schemas'
import { AuthShell } from './AuthShell'

type Values = { identifier: string; password: string }

export function LoginPage() {
  const { login } = useAuth()
  const location = useLocation()
  const notice = (location.state as { notice?: string } | null)?.notice
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<Values>({ resolver: zodResolver(loginSchema) })

  // On success, <RedirectIfAuthenticated> sends the user on to ?next=.
  const submit = handleSubmit(async ({ identifier, password }) => {
    try {
      await login(identifier, password)
    } catch (error) {
      setError('root', {
        message: isApiError(error, 401) ? 'Incorrect username, email or password.' : error instanceof Error ? error.message : 'Sign-in failed.',
      })
    }
  })

  return (
    <AuthShell
      title="Welcome back"
      description="Sign in to bid, sell and manage your listings."
      footer={
        <>
          New here?{' '}
          <Link to={`/register${location.search}`} className="font-medium text-brand-700 hover:underline">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={submit} noValidate className="space-y-5">
        {notice && <Alert tone="success">{notice}</Alert>}
        {errors.root?.message && <Alert tone="error">{errors.root.message}</Alert>}
        <FormField label="Username or email" error={errors.identifier?.message}>
          {(field) => <Input {...field} {...register('identifier')} autoComplete="username" autoFocus />}
        </FormField>
        <div className="space-y-2">
          <FormField label="Password" error={errors.password?.message}>
            {(field) => <Input {...field} {...register('password')} type="password" autoComplete="current-password" />}
          </FormField>
          <div className="flex justify-end">
            <Link to="/forgot-password" className="text-xs font-medium text-brand-700 hover:underline">
              Forgot password?
            </Link>
          </div>
        </div>
        <Button type="submit" size="lg" className="w-full" loading={isSubmitting}>
          Sign in
        </Button>
      </form>
    </AuthShell>
  )
}
