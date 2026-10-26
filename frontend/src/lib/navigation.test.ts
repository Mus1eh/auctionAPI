import { safeNextPath } from './navigation'

describe('safeNextPath', () => {
  it.each([
    ['/products/4', '/products/4'],
    ['/sell?x=1', '/sell?x=1'],
    [null, '/'],
    ['', '/'],
    ['https://evil.example', '/'],
    ['//evil.example', '/'],
    ['/\\evil.example', '/'],
  ])('%s → %s', (input, expected) => {
    expect(safeNextPath(input)).toBe(expected)
  })
})
