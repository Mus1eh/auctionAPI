import { FileSpreadsheet, Upload } from 'lucide-react'
import { useId, useRef, useState } from 'react'
import { toast } from 'sonner'
import { isApiError } from '@/api/client'
import { useImportCsv } from '@/api/queries'
import type { CsvRowError } from '@/api/types'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'

const MAX_BYTES = 2 * 1024 * 1024

function rowErrors(error: unknown): CsvRowError[] {
  if (!isApiError(error) || !error.detail || typeof error.detail !== 'object' || !('errors' in error.detail)) return []
  const errors = (error.detail as { errors: unknown }).errors
  return Array.isArray(errors) ? (errors as CsvRowError[]) : []
}

export function CsvImport() {
  const inputId = useId()
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [localError, setLocalError] = useState<string | null>(null)
  const importCsv = useImportCsv()
  const errors = rowErrors(importCsv.error)

  const choose = (selected: File | null) => {
    importCsv.reset()
    setLocalError(null)
    if (selected && !selected.name.toLowerCase().endsWith('.csv')) {
      setLocalError('Choose a .csv file.')
      setFile(null)
    } else if (selected && selected.size > MAX_BYTES) {
      setLocalError('The file is larger than the 2 MB limit.')
      setFile(null)
    } else {
      setFile(selected)
    }
  }

  const upload = () => {
    if (!file) return
    importCsv.mutate(file, {
      onSuccess: (result) => {
        toast.success(`Imported ${result.imported_count} ${result.imported_count === 1 ? 'listing' : 'listings'} as drafts`)
        setFile(null)
        if (inputRef.current) inputRef.current.value = ''
      },
    })
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-stone-600">
        Upload a UTF-8 CSV (max 2 MB) with exactly these columns:{' '}
        <code className="rounded bg-stone-100 px-1.5 py-0.5 text-xs">name,description,start_price</code>. Every row is imported as a draft. If any row is invalid, nothing is imported.
      </p>
      <label
        htmlFor={inputId}
        className="flex cursor-pointer flex-col items-center gap-2 rounded-xl border border-dashed border-stone-300 bg-stone-50/60 px-4 py-6 text-center transition hover:border-stone-400 hover:bg-stone-50 focus-within:ring-2 focus-within:ring-brand-600"
      >
        <FileSpreadsheet className="size-6 text-stone-400" aria-hidden />
        <span className="text-sm font-medium text-stone-800">{file ? file.name : 'Choose a CSV file'}</span>
        <span className="text-xs text-stone-500">{file ? `${(file.size / 1024).toFixed(1)} KB` : 'Click to browse'}</span>
        <input
          ref={inputRef}
          id={inputId}
          type="file"
          accept=".csv,text/csv"
          className="sr-only"
          onChange={(e) => choose(e.target.files?.[0] ?? null)}
        />
      </label>
      {localError && <Alert tone="error">{localError}</Alert>}
      {importCsv.isError && (
        <Alert tone="error" title={importCsv.error.message}>
          {errors.length > 0 && (
            <ul className="mt-1 max-h-40 list-disc space-y-0.5 overflow-y-auto pl-4 text-xs">
              {errors.map((e) => (
                <li key={e.row}>
                  Row {e.row}: {e.error}
                </li>
              ))}
            </ul>
          )}
        </Alert>
      )}
      <Button onClick={upload} disabled={!file} loading={importCsv.isPending} className="w-full">
        <Upload className="size-4" aria-hidden /> Import listings
      </Button>
    </div>
  )
}
