import { forwardRef, useId, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from 'react'
import { cn } from '@/lib/cn'

const controlBase =
  'block w-full rounded-lg border-0 bg-white text-sm text-stone-900 shadow-sm ring-1 ring-inset ring-stone-300 placeholder:text-stone-400 ' +
  'focus:outline-none focus:ring-2 focus:ring-brand-600 disabled:bg-stone-50 disabled:text-stone-500 ' +
  'aria-[invalid=true]:ring-rose-400 aria-[invalid=true]:focus:ring-rose-500'

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(function Input(
  { className, ...props },
  ref,
) {
  return <input ref={ref} className={cn(controlBase, 'h-10 px-3', className)} {...props} />
})

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(function Textarea(
  { className, ...props },
  ref,
) {
  return <textarea ref={ref} className={cn(controlBase, 'min-h-28 px-3 py-2.5', className)} {...props} />
})

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(function Select(
  { className, ...props },
  ref,
) {
  return <select ref={ref} className={cn(controlBase, 'h-10 pr-8 pl-3', className)} {...props} />
})

interface FormFieldProps {
  label: string
  error?: string
  hint?: ReactNode
  /** Rendered next to the label, e.g. a "Forgot password?" link. */
  aside?: ReactNode
  children: (props: { id: string; 'aria-invalid': boolean; 'aria-describedby'?: string }) => ReactNode
}

export function FormField({ label, error, hint, aside, children }: FormFieldProps) {
  const id = useId()
  const hintId = `${id}-hint`
  const errorId = `${id}-error`
  const describedBy = [hint ? hintId : null, error ? errorId : null].filter(Boolean).join(' ') || undefined

  return (
    <div className="space-y-1.5">
      <div className="flex items-baseline justify-between gap-2">
        <label htmlFor={id} className="text-sm font-medium text-stone-800">
          {label}
        </label>
        {aside}
      </div>
      {children({ id, 'aria-invalid': Boolean(error), 'aria-describedby': describedBy })}
      {hint && !error && (
        <p id={hintId} className="text-xs text-stone-500">
          {hint}
        </p>
      )}
      {error && (
        <p id={errorId} role="alert" className="text-xs font-medium text-rose-600">
          {error}
        </p>
      )}
    </div>
  )
}
