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
export type User = Schemas['UserShow']
export type UserCreate = Schemas['UserCreate']
export type Token = Schemas['Token']

/** Role names seeded by the backend (app/seeders/seeds.py). */
export type Role = 'user' | 'admin' | 'superadmin'

/** GET /admin/dashboard has no response_model; this mirrors app/routers/admin.py. */
export interface AdminDashboard {
  message: string
  username: string
  role: Role
}

/** POST /products/import-csv has no response_model; this mirrors app/routers/product.py. */
export interface CsvImportResult {
  message: string
  imported_count: number
}

export interface CsvRowError {
  row: number
  error: string
}

export const PRODUCT_STATUSES: ProductStatus[] = ['active', 'draft', 'closed', 'sold', 'rejected']
