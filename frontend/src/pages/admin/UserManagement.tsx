import { zodResolver } from '@hookform/resolvers/zod'
import { Search, Trash2, UserRound } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { isApiError } from '@/api/client'
import { useChangeUserRole, useDeleteUser, useRemoveUserRole, useUser } from '@/api/queries'
import type { User } from '@/api/types'
import { useAuth } from '@/auth/AuthContext'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Card, CardHeader } from '@/components/ui/Card'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { FormField, Input, Select } from '@/components/ui/Field'
import { Spinner } from '@/components/ui/States'
import { idSchema } from '@/lib/schemas'

function RoleEditor({ user }: { user: User }) {
  const { can } = useAuth()
  const changeRole = useChangeUserRole()
  const removeRole = useRemoveUserRole()
  const [role, setRole] = useState<'user' | 'admin'>('admin')
  const canAssign = can('user.role.assign')
  const canRemove = can('user.role.remove')

  const announce = (message: string) => ({ onSuccess: () => toast.success(message), onError: (e: Error) => toast.error(e.message) })

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium text-stone-800">Roles</p>
      <ul className="flex flex-wrap gap-1.5" aria-label="Current roles">
        {user.roles.map((name) => (
          <li key={name} className="rounded-full bg-stone-100 px-2.5 py-0.5 text-xs font-medium text-stone-700">
            {name}
          </li>
        ))}
      </ul>
      <div className="flex flex-wrap gap-2">
        <Select aria-label="Role" value={role} onChange={(e) => setRole(e.target.value as 'user' | 'admin')} className="max-w-40">
          <option value="user">user</option>
          <option value="admin">admin</option>
        </Select>
        {canAssign && (
          <Button
            variant="secondary"
            loading={changeRole.isPending}
            onClick={() => changeRole.mutate({ id: user.id, role }, announce(`${user.username} was given the ${role} role`))}
          >
            Add role
          </Button>
        )}
        {canRemove && (
          <Button
            variant="secondary"
            loading={removeRole.isPending}
            onClick={() => removeRole.mutate({ id: user.id, role }, announce(`${user.username} no longer has the ${role} role`))}
          >
            Remove role
          </Button>
        )}
      </div>
      <p className="text-xs text-stone-500">A user can hold several roles but always keeps at least one. Superadmin accounts can’t be modified.</p>
    </div>
  )
}

function UserCard({ user, onDeleted }: { user: User; onDeleted: () => void }) {
  const { can } = useAuth()
  const remove = useDeleteUser()
  const [confirm, setConfirm] = useState(false)

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <span className="flex size-12 items-center justify-center rounded-full bg-stone-100 text-lg font-semibold text-stone-700 uppercase">{user.username[0]}</span>
        <div className="min-w-0">
          <p className="truncate font-semibold text-stone-900">{user.username}</p>
          <p className="truncate text-sm text-stone-500">
            {user.email} · ID {user.id}
          </p>
        </div>
      </div>
      {(can('user.role.assign') || can('user.role.remove')) && <RoleEditor user={user} />}
      <div className="border-t border-stone-100 pt-5">
        <Button variant="danger-ghost" onClick={() => setConfirm(true)}>
          <Trash2 className="size-4" aria-hidden /> Delete user
        </Button>
        <p className="mt-1 text-xs text-stone-500">Only superadmins can delete admins. Superadmin accounts can’t be deleted.</p>
      </div>
      <ConfirmDialog
        open={confirm}
        title={`Delete ${user.username}?`}
        description="The account is permanently deleted. This cannot be undone."
        confirmLabel="Delete user"
        tone="danger"
        loading={remove.isPending}
        onCancel={() => setConfirm(false)}
        onConfirm={() =>
          remove.mutate(user.id, {
            onSuccess: () => {
              toast.success(`${user.username} was deleted`)
              setConfirm(false)
              onDeleted()
            },
            onError: (e) => {
              toast.error(e.message)
              setConfirm(false)
            },
          })
        }
      />
    </div>
  )
}

export function UserManagement() {
  const [userId, setUserId] = useState<number | null>(null)
  const user = useUser(userId)
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<{ id: number }>({ resolver: zodResolver(idSchema) })

  return (
    <Card className="max-w-2xl">
      <CardHeader title="Find a user" description="The API has no user directory, so users are looked up by numeric ID (shown as Bidder # and Seller # across the site)." />
      <div className="space-y-6 p-5 sm:p-6">
        <form onSubmit={handleSubmit(({ id }) => setUserId(id))} noValidate className="flex items-start gap-2">
          <div className="flex-1">
            <FormField label="User ID" error={errors.id?.message}>
              {(field) => <Input {...field} {...register('id', { valueAsNumber: true })} type="number" inputMode="numeric" min={1} placeholder="e.g. 3" />}
            </FormField>
          </div>
          <Button type="submit" className="mt-6.5" loading={user.isFetching}>
            <Search className="size-4" aria-hidden /> Look up
          </Button>
        </form>

        {userId === null ? (
          <div className="flex items-center gap-3 rounded-xl bg-stone-50 p-4 text-sm text-stone-500">
            <UserRound className="size-5" aria-hidden /> Enter an ID to view and manage a user.
          </div>
        ) : user.isPending ? (
          <Spinner />
        ) : user.isError ? (
          <Alert tone={isApiError(user.error, 404) ? 'warning' : 'error'}>
            {isApiError(user.error, 404) ? `No user with ID ${userId}.` : user.error.message}
          </Alert>
        ) : (
          <UserCard user={user.data} onDeleted={() => setUserId(null)} />
        )}
      </div>
    </Card>
  )
}
