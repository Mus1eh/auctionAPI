import { existsSync, readFileSync } from 'node:fs'
import { defineConfig, devices } from '@playwright/test'

// Live-backend credentials stay out of source control in .env.e2e.local (see README).
if (existsSync('.env.e2e.local')) {
  for (const line of readFileSync('.env.e2e.local', 'utf8').split('\n')) {
    const match = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/)
    if (match && !(match[1] in process.env)) process.env[match[1]] = match[2]
  }
}

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 45_000,
  expect: { timeout: 10_000 },
  reporter: [['list']],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:5173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
})
