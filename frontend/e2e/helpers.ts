import { expect, type Page } from '@playwright/test'

/** Fails the test on uncaught exceptions; collects console errors other than HTTP failures we assert on. */
export function trackErrors(page: Page) {
  const errors: string[] = []
  page.on('pageerror', (err) => errors.push(`pageerror: ${err.message}`))
  page.on('console', (msg) => {
    if (msg.type() === 'error' && !msg.text().startsWith('Failed to load resource')) errors.push(`console: ${msg.text()}`)
  })
  return errors
}

export async function register(page: Page, username: string, password: string) {
  await page.goto('/register')
  await page.getByLabel('Username').fill(username)
  await page.getByLabel('Email').fill(`${username}@example.com`)
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByLabel('Confirm password').fill(password)
  await page.getByRole('button', { name: 'Create account' }).click()
  await expect(page.getByRole('button', { name: new RegExp(username) })).toBeVisible()
}

export async function login(page: Page, username: string, password: string) {
  await page.goto('/login')
  await page.getByLabel('Username or email').fill(username)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page.getByRole('button', { name: new RegExp(username) })).toBeVisible()
}

export async function confirmDialog(page: Page, name: string | RegExp) {
  const dialog = page.getByRole('alertdialog')
  await expect(dialog).toBeVisible()
  await dialog.getByRole('button', { name }).click()
  await expect(dialog).toBeHidden()
}
