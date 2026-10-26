import { QueryClientProvider, type QueryClient } from '@tanstack/react-query'
import { Route, Routes } from 'react-router'
import { Toaster } from 'sonner'
import { AuthProvider } from '@/auth/AuthProvider'
import { RedirectIfAuthenticated, RequireAdmin, RequireAuth } from '@/auth/guards'
import { AppLayout } from '@/components/layout/AppLayout'
import { AccountPage } from '@/pages/AccountPage'
import { AdminPage } from '@/pages/admin/AdminPage'
import { ForgotPasswordPage } from '@/pages/auth/ForgotPasswordPage'
import { LoginPage } from '@/pages/auth/LoginPage'
import { RegisterPage } from '@/pages/auth/RegisterPage'
import { ResetPasswordPage } from '@/pages/auth/ResetPasswordPage'
import { EditProductPage } from '@/pages/EditProductPage'
import { MarketplacePage } from '@/pages/MarketplacePage'
import { MyListingsPage } from '@/pages/MyListingsPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { ProductDetailPage } from '@/pages/ProductDetailPage'
import { SellPage } from '@/pages/SellPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<MarketplacePage />} />
        <Route path="products/:id" element={<ProductDetailPage />} />
        <Route path="login" element={<RedirectIfAuthenticated><LoginPage /></RedirectIfAuthenticated>} />
        <Route path="register" element={<RedirectIfAuthenticated><RegisterPage /></RedirectIfAuthenticated>} />
        <Route path="forgot-password" element={<ForgotPasswordPage />} />
        <Route path="reset-password" element={<ResetPasswordPage />} />
        <Route element={<RequireAuth />}>
          <Route path="sell" element={<SellPage />} />
          <Route path="products/:id/edit" element={<EditProductPage />} />
          <Route path="my-listings" element={<MyListingsPage />} />
          <Route path="account" element={<AccountPage />} />
        </Route>
        <Route element={<RequireAdmin />}>
          <Route path="admin" element={<AdminPage />} />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}

export function App({ queryClient }: { queryClient: QueryClient }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <AppRoutes />
        <Toaster position="bottom-right" richColors closeButton />
      </AuthProvider>
    </QueryClientProvider>
  )
}
