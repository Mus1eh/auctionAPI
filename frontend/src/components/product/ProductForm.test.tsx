import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ApiError } from '@/api/client'
import { ProductForm } from './ProductForm'

describe('ProductForm', () => {
  it('blocks submission with invalid values', async () => {
    const onSubmit = vi.fn()
    render(<ProductForm submitLabel="Create draft" onSubmit={onSubmit} />)
    await userEvent.click(screen.getByRole('button', { name: 'Create draft' }))
    expect(await screen.findByText('Name is required')).toBeInTheDocument()
    expect(screen.getByText('Starting price is required')).toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('rejects non-positive prices', async () => {
    const onSubmit = vi.fn()
    render(<ProductForm submitLabel="Create draft" onSubmit={onSubmit} />)
    await userEvent.type(screen.getByLabelText('Title'), 'Desk lamp')
    await userEvent.type(screen.getByLabelText('Starting price'), '0')
    await userEvent.click(screen.getByRole('button', { name: 'Create draft' }))
    expect(await screen.findByText('Starting price must be greater than 0')).toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('submits typed values once and disables the button while saving', async () => {
    let resolve!: () => void
    const onSubmit = vi.fn(() => new Promise<void>((r) => (resolve = r)))
    render(<ProductForm submitLabel="Create draft" onSubmit={onSubmit} />)
    await userEvent.type(screen.getByLabelText('Title'), '  Desk lamp ')
    await userEvent.type(screen.getByLabelText('Description'), 'Brass, working')
    await userEvent.type(screen.getByLabelText('Starting price'), '45')
    const button = screen.getByRole('button', { name: 'Create draft' })
    await userEvent.click(button)
    await waitFor(() => expect(button).toBeDisabled())
    await userEvent.click(button)
    expect(onSubmit).toHaveBeenCalledTimes(1)
    expect(onSubmit.mock.calls[0]).toEqual([{ name: 'Desk lamp', description: 'Brass, working', start_price: 45 }, expect.anything()])
    resolve()
    await waitFor(() => expect(button).toBeEnabled())
  })

  it('shows API errors returned on submit', async () => {
    const onSubmit = vi.fn().mockRejectedValue(new ApiError(403, 'You do not have permission to perform this action.'))
    render(<ProductForm submitLabel="Save" onSubmit={onSubmit} defaultValues={{ name: 'Lamp', description: '', start_price: 5 }} />)
    await userEvent.type(screen.getByLabelText('Title'), '!')
    await userEvent.click(screen.getByRole('button', { name: 'Save' }))
    expect(await screen.findByText('You do not have permission to perform this action.')).toBeInTheDocument()
  })

  it('keeps Save disabled in edit mode until something changes', () => {
    render(<ProductForm submitLabel="Save" onSubmit={vi.fn()} defaultValues={{ name: 'Lamp', description: '', start_price: 5 }} />)
    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled()
  })
})
