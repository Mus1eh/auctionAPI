import { cn } from '@/lib/cn'

export type ButtonVariant = 'primary' | 'brand' | 'secondary' | 'ghost' | 'danger' | 'danger-ghost'
export type ButtonSize = 'sm' | 'md' | 'lg'

const variants: Record<ButtonVariant, string> = {
  primary: 'bg-stone-900 text-white hover:bg-stone-800 shadow-sm',
  brand: 'bg-brand-600 text-white hover:bg-brand-700 shadow-sm',
  secondary: 'bg-white text-stone-800 ring-1 ring-inset ring-stone-300 hover:bg-stone-50 shadow-sm',
  ghost: 'text-stone-700 hover:bg-stone-100',
  danger: 'bg-rose-600 text-white hover:bg-rose-700 shadow-sm',
  'danger-ghost': 'text-rose-700 hover:bg-rose-50',
}

const sizes: Record<ButtonSize, string> = {
  sm: 'h-8 px-3 text-sm gap-1.5 rounded-lg',
  md: 'h-10 px-4 text-sm gap-2 rounded-lg',
  lg: 'h-12 px-5 text-base gap-2 rounded-xl',
}

export function buttonClasses({ variant = 'primary', size = 'md', className }: { variant?: ButtonVariant; size?: ButtonSize; className?: string } = {}) {
  return cn(
    'inline-flex items-center justify-center font-medium whitespace-nowrap transition-colors select-none',
    'disabled:pointer-events-none disabled:opacity-50',
    variants[variant],
    sizes[size],
    className,
  )
}
