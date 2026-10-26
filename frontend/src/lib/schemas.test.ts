import { bidSchema, changePasswordSchema, productSchema, registerSchema } from './schemas'

describe('productSchema', () => {
  it('accepts a valid product', () => {
    expect(productSchema.safeParse({ name: 'Lamp', description: '', start_price: 5 }).success).toBe(true)
  })

  it.each([
    [{ name: ' ', description: '', start_price: 5 }, 'name'],
    [{ name: 'x'.repeat(51), description: '', start_price: 5 }, 'name'],
    [{ name: 'Lamp', description: 'x'.repeat(201), start_price: 5 }, 'description'],
    [{ name: 'Lamp', description: '', start_price: 0 }, 'start_price'],
    [{ name: 'Lamp', description: '', start_price: 1.5 }, 'start_price'],
    [{ name: 'Lamp', description: '', start_price: Number.NaN }, 'start_price'],
  ])('rejects %j on %s', (input, field) => {
    const result = productSchema.safeParse(input)
    expect(result.success).toBe(false)
    expect(result.error?.issues[0].path).toEqual([field])
  })
})

describe('bidSchema', () => {
  it('requires a whole number above the current price', () => {
    const schema = bidSchema(100)
    expect(schema.safeParse({ amount: 101 }).success).toBe(true)
    expect(schema.safeParse({ amount: 100 }).success).toBe(false)
    expect(schema.safeParse({ amount: 100.5 }).success).toBe(false)
  })
})

describe('registerSchema', () => {
  const valid = { username: 'alice', email: 'alice@example.com', password: 'longenough', confirm: 'longenough' }

  it('accepts valid input', () => {
    expect(registerSchema.safeParse(valid).success).toBe(true)
  })

  it('enforces backend limits and matching passwords', () => {
    expect(registerSchema.safeParse({ ...valid, username: 'ab' }).success).toBe(false)
    expect(registerSchema.safeParse({ ...valid, email: 'nope' }).success).toBe(false)
    expect(registerSchema.safeParse({ ...valid, password: 'short', confirm: 'short' }).success).toBe(false)
    const mismatch = registerSchema.safeParse({ ...valid, confirm: 'different1' })
    expect(mismatch.error?.issues[0].path).toEqual(['confirm'])
  })
})

describe('changePasswordSchema', () => {
  it('rejects reusing the current password', () => {
    const result = changePasswordSchema.safeParse({ current: 'samepassword', password: 'samepassword', confirm: 'samepassword' })
    expect(result.error?.issues[0].path).toEqual(['password'])
  })
})
