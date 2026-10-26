import { formatCountdown, timeRemaining } from './format'

describe('timeRemaining', () => {
  const now = Date.parse('2026-01-01T12:00:00Z')

  it('splits the remaining time into parts', () => {
    expect(timeRemaining('2026-01-02T13:02:03Z', now)).toEqual({ totalSeconds: 90123, days: 1, hours: 1, minutes: 2, seconds: 3 })
  })

  it('returns null once the end time has passed or is invalid', () => {
    expect(timeRemaining('2026-01-01T11:59:59Z', now)).toBeNull()
    expect(timeRemaining('2026-01-01T12:00:00Z', now)).toBeNull()
    expect(timeRemaining('not a date', now)).toBeNull()
  })
})

describe('formatCountdown', () => {
  const now = Date.parse('2026-01-01T12:00:00Z')

  it('formats minutes and seconds under an hour', () => {
    expect(formatCountdown('2026-01-01T12:05:09Z', now)).toBe('5m 09s')
  })

  it('formats hours when over an hour', () => {
    expect(formatCountdown('2026-01-01T13:00:30Z', now)).toBe('1h 00m 30s')
  })

  it('formats days when over a day', () => {
    expect(formatCountdown('2026-01-03T15:07:00Z', now)).toBe('2d 3h 07m')
  })

  it('returns null when ended', () => {
    expect(formatCountdown('2026-01-01T11:00:00Z', now)).toBeNull()
  })
})
