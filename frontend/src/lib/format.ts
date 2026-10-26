import { CURRENCY } from './env'

const numberFormat = new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 })
const currencyFormat = CURRENCY
  ? new Intl.NumberFormat(undefined, { style: 'currency', currency: CURRENCY, maximumFractionDigits: 0 })
  : null

export function formatPrice(value: number) {
  return currencyFormat ? currencyFormat.format(value) : numberFormat.format(value)
}

const dateTimeFormat = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' })

export function formatDateTime(value: string | null | undefined) {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '—' : dateTimeFormat.format(date)
}

const relativeFormat = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' })

export function formatRelative(value: string, now = Date.now()) {
  const diffSeconds = Math.round((new Date(value).getTime() - now) / 1000)
  const abs = Math.abs(diffSeconds)
  if (abs < 60) return relativeFormat.format(diffSeconds, 'second')
  if (abs < 3600) return relativeFormat.format(Math.round(diffSeconds / 60), 'minute')
  if (abs < 86400) return relativeFormat.format(Math.round(diffSeconds / 3600), 'hour')
  return relativeFormat.format(Math.round(diffSeconds / 86400), 'day')
}

/** Splits the remaining milliseconds until `endsAt` into display parts; null once it has passed. */
export function timeRemaining(endsAt: string, now = Date.now()) {
  const ms = new Date(endsAt).getTime() - now
  if (Number.isNaN(ms) || ms <= 0) return null
  const totalSeconds = Math.floor(ms / 1000)
  return {
    totalSeconds,
    days: Math.floor(totalSeconds / 86400),
    hours: Math.floor((totalSeconds % 86400) / 3600),
    minutes: Math.floor((totalSeconds % 3600) / 60),
    seconds: totalSeconds % 60,
  }
}

export function formatCountdown(endsAt: string, now = Date.now()) {
  const left = timeRemaining(endsAt, now)
  if (!left) return null
  const pad = (n: number) => String(n).padStart(2, '0')
  if (left.days > 0) return `${left.days}d ${left.hours}h ${pad(left.minutes)}m`
  if (left.hours > 0) return `${left.hours}h ${pad(left.minutes)}m ${pad(left.seconds)}s`
  return `${left.minutes}m ${pad(left.seconds)}s`
}
