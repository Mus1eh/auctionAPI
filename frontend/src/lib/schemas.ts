import { z } from 'zod'

// Limits mirror the backend: pydantic schemas (app/schemas.py) and column sizes (app/models.py).
export const PRODUCT_NAME_MAX = 50
export const PRODUCT_DESCRIPTION_MAX = 200

const positiveInt = (label: string) =>
  z
    .number({ error: `${label} is required` })
    .int(`${label} must be a whole number`)
    .positive(`${label} must be greater than 0`)
    .max(2_147_483_647, `${label} is too large`)

export const productSchema = z.object({
  name: z.string().trim().min(1, 'Name is required').max(PRODUCT_NAME_MAX, `Name must be at most ${PRODUCT_NAME_MAX} characters`),
  description: z
    .string()
    .trim()
    .max(PRODUCT_DESCRIPTION_MAX, `Description must be at most ${PRODUCT_DESCRIPTION_MAX} characters`),
  start_price: positiveInt('Starting price'),
})
export type ProductFormValues = z.infer<typeof productSchema>

export const loginSchema = z.object({
  identifier: z.string().trim().min(1, 'Enter your username or email'),
  password: z.string().min(1, 'Enter your password'),
})

const password = z.string().min(8, 'Password must be at least 8 characters')

export const registerSchema = z
  .object({
    username: z.string().trim().min(3, 'Username must be at least 3 characters').max(50, 'Username must be at most 50 characters'),
    email: z.email('Enter a valid email address').max(100, 'Email must be at most 100 characters'),
    password,
    confirm: z.string(),
  })
  .refine((v) => v.password === v.confirm, { path: ['confirm'], message: 'Passwords do not match' })

export const forgotPasswordSchema = z.object({ email: z.email('Enter a valid email address') })

export const resetPasswordSchema = z
  .object({ password, confirm: z.string() })
  .refine((v) => v.password === v.confirm, { path: ['confirm'], message: 'Passwords do not match' })

export const changePasswordSchema = z
  .object({ current: z.string().min(1, 'Enter your current password'), password, confirm: z.string() })
  .refine((v) => v.password === v.confirm, { path: ['confirm'], message: 'Passwords do not match' })
  .refine((v) => v.password !== v.current, { path: ['password'], message: 'New password must differ from the current one' })

export function bidSchema(currentPrice: number) {
  return z.object({
    amount: positiveInt('Bid').refine((v) => v > currentPrice, `Bid must be greater than ${currentPrice}`),
  })
}

export const idSchema = z.object({ id: positiveInt('ID') })
