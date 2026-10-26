import { PackageX } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'
import { isApiError } from '@/api/client'
import { useMyProducts, usePatchProduct, useProduct } from '@/api/queries'
import type { ProductPatch } from '@/api/types'
import { useAuth } from '@/auth/AuthContext'
import { PageHeader } from '@/components/layout/PageHeader'
import { ProductForm } from '@/components/product/ProductForm'
import { Alert } from '@/components/ui/Alert'
import { buttonClasses } from '@/components/ui/buttonStyles'
import { Card } from '@/components/ui/Card'
import { AccessDenied, EmptyState, ErrorState, PageLoader } from '@/components/ui/States'

export function EditProductPage() {
  const id = Number(useParams().id)
  const navigate = useNavigate()
  const { isAdmin } = useAuth()
  const { data: product, isPending, isError, error, refetch } = useProduct(id)
  const mine = useMyProducts()
  const patch = usePatchProduct(id)

  if (isApiError(error, 404) || !Number.isInteger(id)) {
    return (
      <EmptyState
        icon={PackageX}
        title="Listing not found"
        action={<Link to="/my-listings" className={buttonClasses({ variant: 'secondary' })}>My listings</Link>}
        className="my-10"
      />
    )
  }
  if (isPending || mine.isPending) return <PageLoader />
  if (isError) return <ErrorState error={error} onRetry={() => refetch()} />

  const isOwner = mine.data?.some((p) => p.id === id) ?? false
  if (!isOwner && !isAdmin) return <AccessDenied message="Only the seller or an admin can edit this listing." />

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <PageHeader eyebrow={`Lot #${product.id}`} title="Edit listing" />
      {product.status !== 'draft' && (
        <Alert tone="warning" title="This listing is no longer a draft">
          Changing the starting price does not change the current bid of {product.current_price}.
        </Alert>
      )}
      <Card className="p-5 sm:p-8">
        <ProductForm
          submitLabel="Save changes"
          defaultValues={{ name: product.name, description: product.description ?? '', start_price: product.start_price }}
          onCancel={() => navigate(`/products/${id}`)}
          onSubmit={async (values, dirty) => {
            const changes: ProductPatch = {}
            if (dirty.name) changes.name = values.name
            if (dirty.description) changes.description = values.description || null
            if (dirty.start_price) changes.start_price = values.start_price
            await patch.mutateAsync(changes)
            toast.success('Listing updated')
            navigate(`/products/${id}`)
          }}
        />
      </Card>
    </div>
  )
}
