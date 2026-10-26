import { cn } from '@/lib/cn'

/**
 * The API has no product images, so each listing gets a deterministic generated
 * cover derived from its id and name instead of a stock photo or broken URL.
 */
function hash(input: string) {
  let h = 0
  for (let i = 0; i < input.length; i++) h = (Math.imul(31, h) + input.charCodeAt(i)) | 0
  return Math.abs(h)
}

function initials(name: string) {
  const words = name.trim().split(/\s+/).filter(Boolean)
  if (!words.length) return '#'
  return (words.length === 1 ? words[0].slice(0, 2) : words[0][0] + words[1][0]).toUpperCase()
}

export function ProductArt({ id, name, className, size = 'md' }: { id: number; name: string; className?: string; size?: 'md' | 'lg' }) {
  const h = hash(`${id}:${name}`)
  const hue = h % 360
  const hue2 = (hue + 35 + (h % 50)) % 360
  const angle = 120 + (h % 120)

  return (
    <div
      aria-hidden
      className={cn('relative isolate overflow-hidden', className)}
      style={{
        backgroundImage: `linear-gradient(${angle}deg, hsl(${hue} 45% 92%), hsl(${hue2} 50% 82%))`,
      }}
    >
      <div
        className="absolute inset-0 opacity-[0.35]"
        style={{
          backgroundImage: `radial-gradient(circle at ${20 + (h % 60)}% ${15 + (h % 50)}%, hsl(${hue2} 70% 96%) 0, transparent 55%)`,
        }}
      />
      <div className="absolute inset-0 flex items-center justify-center">
        <span
          className={cn('font-semibold tracking-tight', size === 'lg' ? 'text-7xl sm:text-8xl' : 'text-5xl')}
          style={{ color: `hsl(${hue} 35% 30% / 0.55)` }}
        >
          {initials(name)}
        </span>
      </div>
    </div>
  )
}
