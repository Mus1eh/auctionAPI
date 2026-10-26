import { expect, test, type Browser, type Page } from '@playwright/test'
import { confirmDialog, login, register, trackErrors } from './helpers'

/**
 * Full auction lifecycle against the real FastAPI backend:
 * seller lists → requests go-live → admin approves → bidder bids → admin closes → seller accepts.
 */
const run = Date.now().toString(36)
const seller = { username: `seller_${run}`, password: 'seller-pass-123' }
const bidder = { username: `bidder_${run}`, password: 'bidder-pass-123' }
const admin = { username: process.env.E2E_SUPERADMIN_USERNAME ?? '', password: process.env.E2E_SUPERADMIN_PASSWORD ?? '' }
const productName = `E2E Camera ${run}`

let productUrl = ''

async function newPage(browser: Browser): Promise<[Page, string[]]> {
  const page = await (await browser.newContext()).newPage()
  return [page, trackErrors(page)]
}

test.describe.serial('auction lifecycle', () => {
  test.skip(!admin.username || !admin.password, 'Set E2E_SUPERADMIN_USERNAME / E2E_SUPERADMIN_PASSWORD (see README)')

  test('public pages render and protected routes redirect', async ({ page }) => {
    const errors = trackErrors(page)
    await page.goto('/')
    await expect(page.getByRole('heading', { level: 1 })).toContainText('Bid on one-of-a-kind finds')
    await expect(page.getByRole('tab', { name: /live now/i })).toHaveAttribute('aria-selected', 'true')

    await page.goto('/sell')
    await expect(page).toHaveURL(/\/login\?next=%2Fsell$/)

    await page.goto('/does-not-exist')
    await expect(page.getByText('Page not found')).toBeVisible()
    expect(errors).toEqual([])
  })

  test('login rejects bad credentials', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('Username or email').fill(`nobody_${run}`)
    await page.getByLabel('Password').fill('wrong-password')
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page.getByText('Incorrect username, email or password.')).toBeVisible()
  })

  test('seller registers, creates a draft and requests go-live', async ({ browser }) => {
    const [page, errors] = await newPage(browser)
    await register(page, seller.username, seller.password)

    await page.getByRole('link', { name: 'New listing' }).click()
    await page.getByRole('button', { name: 'Create draft' }).click()
    await expect(page.getByText('Name is required')).toBeVisible()

    await page.getByLabel('Title').fill(productName)
    await page.getByLabel('Description').fill('Rangefinder in great condition. Strap included.')
    await page.getByLabel('Starting price').fill('100')
    await page.getByRole('button', { name: 'Create draft' }).click()

    await expect(page).toHaveURL(/\/products\/\d+$/)
    productUrl = new URL(page.url()).pathname
    await expect(page.getByRole('heading', { name: productName })).toBeVisible()
    await expect(page.getByText('Your listing', { exact: true })).toBeVisible()

    await page.getByRole('button', { name: 'Request to go live' }).click()
    await expect(page.getByText('Awaiting admin review')).toBeVisible()

    // A second request is refused by the backend (409) and surfaces as "already pending".
    await page.reload()
    await page.getByRole('button', { name: 'Request to go live' }).click()
    await expect(page.getByText(/already pending/)).toBeVisible()
    expect(errors).toEqual([])
  })

  test('a regular user cannot open the admin console', async ({ browser }) => {
    const [page] = await newPage(browser)
    await login(page, seller.username, seller.password)
    await page.goto('/admin')
    await expect(page.getByText('Access denied')).toBeVisible()
    await expect(page.getByRole('link', { name: 'Admin' })).toHaveCount(0)
  })

  test('admin approves the go-live request', async ({ browser }) => {
    const [page, errors] = await newPage(browser)
    await login(page, admin.username, admin.password)
    await page.getByRole('link', { name: 'Admin' }).click()
    await expect(page.getByText('Welcome to the admin dashboard!')).toBeVisible()

    await page.getByRole('tab', { name: /requests/i }).click()
    const row = page.getByRole('listitem').filter({ hasText: productName })
    await row.getByRole('button', { name: 'Approve' }).click()
    await confirmDialog(page, 'Approve')
    await expect(page.getByText(/approved\. The auction is now live/)).toBeVisible()
    await expect(row).toHaveCount(0)
    expect(errors).toEqual([])
  })

  test('bidder places bids on the live auction', async ({ browser }) => {
    const [page, errors] = await newPage(browser)
    await register(page, bidder.username, bidder.password)
    await page.goto('/')
    await page.getByLabel('Search listings').fill(run)
    await page.getByRole('link', { name: productName }).click()
    await expect(page).toHaveURL(productUrl)
    await expect(page.getByText('Accepting bids now')).toBeVisible()
    await expect(page.getByText(/left$/).or(page.getByText(/^\d+m \d+s$/)).first()).toBeVisible()

    await page.getByLabel('Your bid').fill('100')
    await page.getByRole('button', { name: 'Place bid' }).click()
    await expect(page.getByText('Bid must be greater than 100')).toBeVisible()

    await page.getByLabel('Your bid').fill('125')
    await page.getByRole('button', { name: 'Place bid' }).click()
    await expect(page.getByText(/Bid of 125 placed/)).toBeVisible()
    await expect(page.getByText('Current bid')).toBeVisible()
    await expect(page.getByRole('cell', { name: '125' })).toBeVisible()

    // Quick-bid chip (+1%) → 127
    await page.getByRole('button', { name: '127' }).click()
    await page.getByRole('button', { name: 'Place bid' }).click()
    await expect(page.getByText(/Bid of 127 placed/)).toBeVisible()
    await expect(page.getByRole('row').nth(1)).toContainText('Highest')
    await expect(page.getByRole('row').nth(1)).toContainText('127')
    expect(errors).toEqual([])
  })

  test('seller cannot bid on their own listing', async ({ browser }) => {
    const [page] = await newPage(browser)
    await login(page, seller.username, seller.password)
    await page.goto(productUrl)
    await expect(page.getByText('This is your listing, so you can’t bid on it.')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Place bid' })).toHaveCount(0)
  })

  test('admin closes the auction early and the seller accepts the highest bid', async ({ browser }) => {
    const [adminPage, adminErrors] = await newPage(browser)
    await login(adminPage, admin.username, admin.password)
    await adminPage.goto(productUrl)
    await adminPage.getByRole('button', { name: 'Close auction now' }).click()
    await confirmDialog(adminPage, 'Close auction')
    await expect(adminPage.getByText('Auction closed')).toBeVisible()
    await expect(adminPage.getByText('Bidding closed, awaiting the seller’s decision')).toBeVisible()

    const [page, errors] = await newPage(browser)
    await login(page, seller.username, seller.password)
    await page.goto('/my-listings')
    await expect(page.getByText('Awaiting your decision')).toBeVisible()
    await page.getByRole('link', { name: new RegExp(productName) }).click()
    await expect(page.getByText(/127\s*by Bidder #\d+/)).toBeVisible()
    await page.getByRole('button', { name: 'Accept & sell' }).click()
    await confirmDialog(page, 'Accept & sell')
    await expect(page.getByText(new RegExp(`Sold to ${bidder.username} for 127`))).toBeVisible()
    await expect(page.getByText('Sold for')).toBeVisible()
    expect([...adminErrors, ...errors]).toEqual([])
  })

  test('seller edits and deletes a listing', async ({ browser }) => {
    const [page, errors] = await newPage(browser)
    await login(page, seller.username, seller.password)
    await page.goto('/sell')
    await page.getByLabel('Title').fill(`Temp lamp ${run}`)
    await page.getByLabel('Starting price').fill('20')
    await page.getByRole('button', { name: 'Create draft' }).click()
    await expect(page.getByRole('heading', { name: `Temp lamp ${run}` })).toBeVisible()

    await page.getByRole('link', { name: 'Edit' }).click()
    await page.getByLabel('Title').fill(`Brass lamp ${run}`)
    await page.getByRole('button', { name: 'Save changes' }).click()
    await expect(page.getByRole('heading', { name: `Brass lamp ${run}` })).toBeVisible()

    await page.getByRole('button', { name: 'Delete' }).click()
    await confirmDialog(page, 'Delete listing')
    await expect(page).toHaveURL(/\/my-listings$/)
    await expect(page.getByText(`Brass lamp ${run}`)).toHaveCount(0)
    expect(errors).toEqual([])
  })

  test('CSV import reports row errors and imports valid files', async ({ browser }) => {
    const [page, errors] = await newPage(browser)
    await login(page, seller.username, seller.password)
    await page.goto('/my-listings')

    await page.getByLabel(/choose a csv file/i).setInputFiles({
      name: 'bad.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from(`name,description,start_price\nGood ${run},ok,10\nBad ${run},bad,-5\n`),
    })
    await page.getByRole('button', { name: 'Import listings' }).click()
    await expect(page.getByText('CSV validation failed, No products were imported.')).toBeVisible()
    await expect(page.getByText(/^Row 3:/)).toBeVisible()

    await page.getByLabel(/bad\.csv/).setInputFiles({
      name: 'good.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from(`name,description,start_price\nCsv chair ${run},Oak,15\nCsv desk ${run},,40\n`),
    })
    await page.getByRole('button', { name: 'Import listings' }).click()
    await expect(page.getByText('Imported 2 listings as drafts')).toBeVisible()
    await expect(page.getByText(`Csv chair ${run}`)).toBeVisible()
    expect(errors).toEqual([])
  })

  test('superadmin looks up a user and changes their role', async ({ browser }) => {
    const [page, errors] = await newPage(browser)
    await login(page, admin.username, admin.password)
    await page.goto(productUrl)
    const bidderId = (await page.getByText(/^Bidder #\d+$/).first().textContent())!.replace(/\D/g, '')

    await page.goto('/admin?tab=users')
    await page.getByLabel('User ID').fill(bidderId)
    await page.getByRole('button', { name: 'Look up' }).click()
    await expect(page.getByText(`${bidder.username}@example.com · ID ${bidderId}`)).toBeVisible()

    await page.getByLabel('New role').selectOption('admin')
    await page.getByRole('button', { name: 'Apply' }).click()
    await expect(page.getByText(`${bidder.username} is now an admin`)).toBeVisible()

    // Backend refuses to delete admins; the error is surfaced.
    await page.getByRole('button', { name: 'Delete user' }).click()
    await confirmDialog(page, 'Delete user')
    await expect(page.getByText('You do not have permission to perform this action.')).toBeVisible()

    await page.getByLabel('New role').selectOption('user')
    await page.getByRole('button', { name: 'Apply' }).click()
    await expect(page.getByText(`${bidder.username} is now a user`)).toBeVisible()
    expect(errors).toEqual([])
  })

  test('session survives reload and sign-out clears it', async ({ browser }) => {
    const [page, errors] = await newPage(browser)
    await login(page, bidder.username, bidder.password)
    await page.reload()
    await expect(page.getByRole('button', { name: new RegExp(bidder.username) })).toBeVisible()

    await page.getByRole('button', { name: new RegExp(bidder.username) }).click()
    await page.getByRole('menuitem', { name: 'Sign out' }).click()
    await expect(page.getByRole('link', { name: 'Sign in' })).toBeVisible()
    await page.reload()
    await expect(page.getByRole('link', { name: 'Sign in' })).toBeVisible()
    expect(errors).toEqual([])
  })
})

test.describe('mobile layout', () => {
  test.use({ viewport: { width: 390, height: 844 } })

  test('menu opens, navigates and the page does not scroll sideways', async ({ page }) => {
    const errors = trackErrors(page)
    await page.goto('/')
    await expect(page.getByRole('navigation', { name: 'Main' })).toBeHidden()
    await page.getByRole('button', { name: 'Open menu' }).click()
    const mobileNav = page.locator('#mobile-nav')
    await expect(mobileNav).toBeVisible()
    await mobileNav.getByRole('link', { name: 'Sign in' }).click()
    await expect(page).toHaveURL(/\/login/)
    await expect(mobileNav).toBeHidden()

    for (const path of ['/', '/login', '/register', productUrl || '/']) {
      await page.goto(path)
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
      expect(overflow, `horizontal overflow on ${path}`).toBeLessThanOrEqual(0)
    }
    expect(errors).toEqual([])
  })
})
