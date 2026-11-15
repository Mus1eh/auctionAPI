import type { components } from './schema'

type Schemas = components['schemas']

export type Product = Schemas['ProductShow']
export type ProductCreate = Schemas['ProductCreate']
export type ProductPatch = Schemas['ProductPatch']
export type ProductStatus = Schemas['ProductStatus']
export type ProductApproval = Schemas['ProductApprovalShow']
export type StatusRequest = Schemas['ProductStatusRequestShow']
export type Bid = Schemas['BidShow']
export type BidDecision = Schemas['ApproveBidding']
/** A user as admins see them: with role names. */
export type User = Schemas['UserDetail']
/** The signed-in user: role names plus every permission those roles grant. */
export type Me = Schemas['UserMe']
export type UserCreate = Schemas['UserCreate']
export type Token = Schemas['Token']

/** A page of a list endpoint: the rows on this page and the total across all pages. */
export interface Page<T> {
  items: T[]
  total: number
}

/** Role names seeded by the backend (app/seeders/seeds.py). */
export type Role = 'user' | 'admin' | 'superadmin'

/** GET /admin/dashboard has no response_model; this mirrors app/routers/admin.py. */
export interface AdminDashboard {
  message: string
  username: string
  roles: string[]
}

/** POST /products/import-csv answers 202 once the file is queued; this mirrors app/routers/product.py. */
export interface CsvImportQueued {
  task_id: string
}

export interface CsvImportFailure {
  message: string
  errors: CsvRowError[]
}

/**
 * GET /products/import-csv/{task_id}. "failed" means the file was read but is invalid
 * (nothing was imported); "error" means the worker itself crashed.
 */
export type CsvImportStatus =
  | { status: 'processing' }
  | { status: 'success'; message: string; imported_count: number }
  | { status: 'failed'; detail: string | CsvImportFailure }
  | { status: 'error'; detail: string }

export interface CsvImportResult {
  message: string
  imported_count: number
}

export interface CsvRowError {
  row: number
  error: string
}

export const PRODUCT_STATUSES: ProductStatus[] = ['active', 'draft', 'closed', 'sold', 'rejected']

/** Statuses the API only returns to their owner (requires sign-in). */
export const PRIVATE_PRODUCT_STATUSES: ProductStatus[] = ['draft', 'rejected']

export function isPrivateStatus(status: ProductStatus): boolean {
  return PRIVATE_PRODUCT_STATUSES.includes(status)
}
