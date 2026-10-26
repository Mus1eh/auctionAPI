import { useNavigate } from 'react-router'
import { toast } from 'sonner'
import { useCreateProduct } from '@/api/queries'
import { PageHeader } from '@/components/layout/PageHeader'
import { ProductForm } from '@/components/product/ProductForm'
import { Card } from '@/components/ui/Card'

const STEPS = [
  ['Create a draft', 'Add a title, description and starting price.'],
  ['Request to go live', 'Send the draft to an admin for review.'],
  ['One-hour auction', 'Once approved, bidding runs for exactly one hour.'],
  ['Accept or decline', 'When it ends, you decide on the highest bid.'],
]

export function SellPage() {
  const navigate = useNavigate()
  const create = useCreateProduct()

  return (
    <div className="space-y-8">
      <PageHeader eyebrow="Sell" title="Create a listing" description="New listings start as drafts. Nobody can bid until an admin approves your listing." />
      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_320px]">
        <Card className="p-5 sm:p-8">
          <ProductForm
            submitLabel="Create draft"
            onCancel={() => navigate(-1)}
            onSubmit={async (values) => {
              const product = await create.mutateAsync({
                name: values.name,
                description: values.description || null,
                start_price: values.start_price,
              })
              toast.success('Draft created', { description: 'Request to go live when you’re ready.' })
              navigate(`/products/${product.id}`)
            }}
          />
        </Card>
        <aside>
          <h2 className="text-sm font-semibold text-stone-900">How selling works</h2>
          <ol className="mt-4 space-y-4">
            {STEPS.map(([title, body], i) => (
              <li key={title} className="flex gap-3">
                <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-stone-900 text-xs font-semibold text-white">{i + 1}</span>
                <div>
                  <p className="text-sm font-medium text-stone-900">{title}</p>
                  <p className="text-sm text-stone-500">{body}</p>
                </div>
              </li>
            ))}
          </ol>
        </aside>
      </div>
    </div>
  )
}
