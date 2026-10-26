import { zodResolver } from '@hookform/resolvers/zod'
import { useForm, useWatch } from 'react-hook-form'
import { isApiError } from '@/api/client'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { FormField, Input, Textarea } from '@/components/ui/Field'
import { PRODUCT_DESCRIPTION_MAX, productSchema, type ProductFormValues } from '@/lib/schemas'

interface ProductFormProps {
  defaultValues?: ProductFormValues
  submitLabel: string
  onSubmit: (values: ProductFormValues, dirty: Partial<Record<keyof ProductFormValues, boolean>>) => Promise<unknown>
  onCancel?: () => void
}

export function ProductForm({ defaultValues, submitLabel, onSubmit, onCancel }: ProductFormProps) {
  const {
    register,
    handleSubmit,
    control,
    setError,
    formState: { errors, isSubmitting, dirtyFields, isDirty },
  } = useForm<ProductFormValues>({
    resolver: zodResolver(productSchema),
    defaultValues: defaultValues ?? { name: '', description: '', start_price: undefined as unknown as number },
  })

  const descriptionLength = useWatch({ control, name: 'description' })?.length ?? 0

  const submit = handleSubmit(async (values) => {
    try {
      await onSubmit(values, dirtyFields)
    } catch (error) {
      let mapped = false
      if (isApiError(error)) {
        for (const fieldError of error.fieldErrors) {
          if (fieldError.field === 'name' || fieldError.field === 'description' || fieldError.field === 'start_price') {
            setError(fieldError.field, { message: fieldError.message })
            mapped = true
          }
        }
      }
      if (!mapped) setError('root', { message: error instanceof Error ? error.message : 'Could not save the listing.' })
    }
  })

  return (
    <form onSubmit={submit} noValidate className="space-y-5">
      {errors.root?.message && <Alert tone="error">{errors.root.message}</Alert>}

      <FormField label="Title" error={errors.name?.message}>
        {(field) => <Input {...field} {...register('name')} placeholder="e.g. Vintage Omega Seamaster, 1968" autoComplete="off" />}
      </FormField>

      <FormField
        label="Description"
        error={errors.description?.message}
        hint={`${descriptionLength}/${PRODUCT_DESCRIPTION_MAX} characters · Optional`}
      >
        {(field) => (
          <Textarea {...field} {...register('description')} placeholder="Condition, provenance, what's included…" maxLength={PRODUCT_DESCRIPTION_MAX} />
        )}
      </FormField>

      <FormField label="Starting price" error={errors.start_price?.message} hint="Whole numbers only. Bids must exceed the current price.">
        {(field) => (
          <Input
            {...field}
            {...register('start_price', { valueAsNumber: true })}
            type="number"
            inputMode="numeric"
            min={1}
            step={1}
            placeholder="100"
            className="tabular sm:max-w-48"
          />
        )}
      </FormField>

      <div className="flex flex-col-reverse gap-2 border-t border-stone-100 pt-5 sm:flex-row sm:justify-end">
        {onCancel && (
          <Button variant="secondary" onClick={onCancel} disabled={isSubmitting}>
            Cancel
          </Button>
        )}
        <Button type="submit" loading={isSubmitting} disabled={Boolean(defaultValues) && !isDirty}>
          {submitLabel}
        </Button>
      </div>
    </form>
  )
}
