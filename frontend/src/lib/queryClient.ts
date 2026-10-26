import { QueryClient } from '@tanstack/react-query'
import { isApiError } from '@/api/client'

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 15_000,
        // Client errors (4xx) won't change on retry; network/5xx errors get two more attempts.
        retry: (failureCount, error) => !(isApiError(error) && error.status >= 400 && error.status < 500) && failureCount < 2,
      },
    },
  })
}
