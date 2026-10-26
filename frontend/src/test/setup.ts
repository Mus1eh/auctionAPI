import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'
import { tokenStore } from '@/api/tokens'

// Unmount first so clearing the session doesn't update a mounted AuthProvider.
afterEach(() => {
  cleanup()
  tokenStore.clear()
  localStorage.clear()
  vi.unstubAllGlobals()
})
