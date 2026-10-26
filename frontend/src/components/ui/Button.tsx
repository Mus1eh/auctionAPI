import { Loader2 } from 'lucide-react'
import type { ComponentProps } from 'react'
import { buttonClasses, type ButtonSize, type ButtonVariant } from './buttonStyles'

interface ButtonProps extends ComponentProps<'button'> {
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
}

export function Button({ variant, size, loading, className, children, disabled, type = 'button', ...props }: ButtonProps) {
  return (
    <button
      type={type}
      className={buttonClasses({ variant, size, className })}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading && <Loader2 className="size-4 animate-spin" aria-hidden />}
      {children}
    </button>
  )
}
