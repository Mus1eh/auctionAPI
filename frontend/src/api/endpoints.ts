import { apiRequest, isApiError } from './client'
import type {
  AdminDashboard,
  Bid,
  BidDecision,
  CsvImportResult,
  Product,
  ProductApproval,
  ProductCreate,
  ProductPatch,
  ProductStatus,
  Role,
  StatusRequest,
  Token,
  User,
  UserCreate,
} from './types'

/** Some list endpoints answer 404 instead of an empty array when nothing matches. */
async function emptyOn404<T>(promise: Promise<T[]>): Promise<T[]> {
  try {
    return await promise
  } catch (error) {
    if (isApiError(error, 404)) return []
    throw error
  }
}

export const authApi = {
  login(username: string, password: string) {
    const body = new URLSearchParams({ grant_type: 'password', username, password })
    return apiRequest<Token>('/auth/', { method: 'POST', body })
  },
  logout(refreshToken: string) {
    return apiRequest<void>('/auth/logout', { method: 'POST', json: { refresh_token: refreshToken } })
  },
  logoutAll() {
    return apiRequest<{ message: string; count: number }>('/auth/logout-all', { method: 'POST', auth: true })
  },
  forgotPassword(email: string) {
    return apiRequest<{ message: string }>('/auth/forgot-password', { method: 'POST', json: { email } })
  },
  verifyResetToken(resetToken: string) {
    return apiRequest<unknown>('/auth/verify-token', { method: 'POST', json: { reset_token: resetToken } })
  },
  resetPassword(token: string, newPassword: string) {
    return apiRequest<{ message: string }>('/auth/reset-password', {
      method: 'POST',
      json: { token, new_password: newPassword },
    })
  },
  changePassword(currentPassword: string, newPassword: string) {
    return apiRequest<{ message: string }>('/auth/change-password', {
      method: 'POST',
      auth: true,
      json: { current_password: currentPassword, new_password: newPassword },
    })
  },
}

export const usersApi = {
  register(data: UserCreate) {
    return apiRequest<User>('/users/', { method: 'POST', json: data })
  },
  get(id: number) {
    return apiRequest<User>(`/users/${id}`, { auth: true })
  },
  remove(id: number) {
    return apiRequest<{ message: string }>(`/users/${id}`, { method: 'DELETE', auth: true })
  },
}

export const productsApi = {
  listByStatus(status: ProductStatus) {
    return emptyOn404(apiRequest<Product[]>(`/products/status/${status}`))
  },
  mine() {
    return emptyOn404(apiRequest<Product[]>('/products/my', { auth: true }))
  },
  get(id: number) {
    return apiRequest<Product>(`/products/${id}`)
  },
  create(data: ProductCreate) {
    return apiRequest<Product>('/products/', { method: 'POST', auth: true, json: data })
  },
  patch(id: number, data: ProductPatch) {
    return apiRequest<Product>(`/products/${id}`, { method: 'PATCH', auth: true, json: data })
  },
  remove(id: number) {
    return apiRequest<{ detail: string }>(`/products/${id}`, { method: 'DELETE', auth: true })
  },
  requestStatus(id: number, status: ProductStatus) {
    return apiRequest<StatusRequest>(`/products/${id}/status-request`, {
      method: 'POST',
      auth: true,
      query: { request: status },
    })
  },
  importCsv(file: File) {
    const body = new FormData()
    body.append('file', file)
    return apiRequest<CsvImportResult>('/products/import-csv', { method: 'POST', auth: true, body })
  },
}

export const BIDS_PAGE_SIZE = 10

export const bidsApi = {
  list(productId: number, page: number, limit = BIDS_PAGE_SIZE) {
    return apiRequest<Bid[]>(`/bids/${productId}`, { query: { page, limit } })
  },
  place(productId: number, amount: number) {
    return apiRequest<Bid>(`/bids/${productId}`, { method: 'POST', auth: true, json: { amount } })
  },
  decide(productId: number, decision: BidDecision) {
    return apiRequest<ProductApproval>(`/bids/${productId}/approve`, {
      method: 'POST',
      auth: true,
      query: { request: decision },
    })
  },
}

export const adminApi = {
  dashboard() {
    return apiRequest<AdminDashboard>('/admin/dashboard', { auth: true })
  },
  pendingRequests() {
    return apiRequest<StatusRequest[]>('/admin/status-request/pending', { auth: true })
  },
  approveRequest(id: number) {
    return apiRequest<StatusRequest>(`/admin/status-requests/${id}/approve`, { method: 'PATCH', auth: true })
  },
  rejectRequest(id: number) {
    return apiRequest<StatusRequest>(`/admin/status-requests/${id}/reject`, { method: 'PATCH', auth: true })
  },
  setProductStatus(productId: number, status: Extract<ProductStatus, 'active' | 'closed'>) {
    return apiRequest<Product>(`/admin/products/${productId}/status/${status}`, { method: 'POST', auth: true })
  },
  changeUserRole(userId: number, role: Exclude<Role, 'superadmin'>) {
    return apiRequest<User>(`/admin/users/${userId}/role`, { method: 'PATCH', auth: true, json: { role_name: role } })
  },
}
