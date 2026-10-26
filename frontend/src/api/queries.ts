import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { adminApi, bidsApi, productsApi, usersApi } from "./endpoints";
import type {
  BidDecision,
  ProductCreate,
  ProductPatch,
  ProductStatus,
  Role,
} from "./types";

export const queryKeys = {
  products: ["products"] as const,
  productsByStatus: (status: ProductStatus) =>
    ["products", "status", status] as const,
  product: (id: number) => ["products", "detail", id] as const,
  myProducts: ["my-products"] as const,
  bids: (productId: number) => ["bids", productId] as const,
  bidsPage: (productId: number, page: number) =>
    ["bids", productId, page] as const,
  pendingRequests: ["admin", "pending-requests"] as const,
  adminDashboard: ["admin", "dashboard"] as const,
  user: (id: number) => ["users", id] as const,
};

/** Query roots holding per-user data; dropped from the cache on sign-out. */
export const PRIVATE_QUERY_ROOTS = ["my-products", "admin", "users"];

/** The API has no push channel; active auctions are polled (as suggested in app/routers/bids.py). */
export const LIVE_POLL_MS = 3000;

export function useProductsByStatus(status: ProductStatus) {
  return useQuery({
    queryKey: queryKeys.productsByStatus(status),
    queryFn: () => productsApi.listByStatus(status),
    refetchInterval: status === "active" ? LIVE_POLL_MS * 3 : false,
  });
}

export function useProduct(id: number) {
  return useQuery({
    queryKey: queryKeys.product(id),
    queryFn: () => productsApi.get(id),
    enabled: Number.isInteger(id) && id > 0,
    refetchInterval: (query) =>
      query.state.data?.status === "active" ? LIVE_POLL_MS : false,
  });
}

export function useMyProducts(enabled = true) {
  return useQuery({
    queryKey: queryKeys.myProducts,
    queryFn: productsApi.mine,
    enabled,
  });
}

export function useBids(productId: number, page: number, live: boolean) {
  return useQuery({
    queryKey: queryKeys.bidsPage(productId, page),
    queryFn: () => bidsApi.list(productId, page),
    enabled: Number.isInteger(productId) && productId > 0,
    placeholderData: keepPreviousData,
    refetchInterval: live ? LIVE_POLL_MS : false,
  });
}

export function useAdminDashboard() {
  return useQuery({
    queryKey: queryKeys.adminDashboard,
    queryFn: adminApi.dashboard,
  });
}

export function usePendingRequests() {
  return useQuery({
    queryKey: queryKeys.pendingRequests,
    queryFn: adminApi.pendingRequests,
  });
}

export function useUser(id: number | null) {
  return useQuery({
    queryKey: queryKeys.user(id ?? 0),
    queryFn: () => usersApi.get(id!),
    enabled: id !== null,
    retry: false,
  });
}

/**
 * Refetches product data in the background. Deliberately not awaited by mutations: a slow
 * or retrying refetch must not keep the triggering button/dialog in its loading state.
 */
function useInvalidateProducts() {
  const queryClient = useQueryClient();
  return (productId?: number) => {
    void Promise.all([
      queryClient.invalidateQueries({ queryKey: queryKeys.products }),
      queryClient.invalidateQueries({ queryKey: queryKeys.myProducts }),
      productId !== undefined &&
        queryClient.invalidateQueries({ queryKey: queryKeys.bids(productId) }),
    ]);
  };
}

export function usePlaceBid(productId: number) {
  const invalidate = useInvalidateProducts();
  return useMutation({
    mutationFn: (amount: number) => bidsApi.place(productId, amount),
    onSettled: () => invalidate(productId),
  });
}

export function useDecideBid(productId: number) {
  const invalidate = useInvalidateProducts();
  return useMutation({
    mutationFn: (decision: BidDecision) => bidsApi.decide(productId, decision),
    onSettled: () => invalidate(productId),
  });
}

export function useCreateProduct() {
  const invalidate = useInvalidateProducts();
  return useMutation({
    mutationFn: (data: ProductCreate) => productsApi.create(data),
    onSuccess: () => invalidate(),
  });
}

export function usePatchProduct(id: number) {
  const invalidate = useInvalidateProducts();
  return useMutation({
    mutationFn: (data: ProductPatch) => productsApi.patch(id, data),
    onSuccess: () => invalidate(id),
  });
}

export function useDeleteProduct() {
  const queryClient = useQueryClient();
  const invalidate = useInvalidateProducts();
  return useMutation({
    mutationFn: (id: number) => productsApi.remove(id),
    onSuccess: (_data, id) => {
      queryClient.removeQueries({ queryKey: queryKeys.product(id) });
      invalidate();
    },
  });
}

export function useRequestGoLive() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => productsApi.requestStatus(id, "active"),
    onSettled: () =>
      void queryClient.invalidateQueries({
        queryKey: queryKeys.pendingRequests,
      }),
  });
}

export function useImportCsv() {
  const invalidate = useInvalidateProducts();
  return useMutation({
    mutationFn: (file: File) => productsApi.importCsv(file),
    onSuccess: () => invalidate(),
  });
}

export function useReviewRequest() {
  const queryClient = useQueryClient();
  const invalidate = useInvalidateProducts();
  return useMutation({
    mutationFn: ({ id, approve }: { id: number; approve: boolean }) =>
      approve ? adminApi.approveRequest(id) : adminApi.rejectRequest(id),
    onSettled: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.pendingRequests,
      });
      invalidate();
    },
  });
}

export function useSetProductStatus() {
  const invalidate = useInvalidateProducts();
  return useMutation({
    mutationFn: ({ id, status }: { id: number; status: "active" | "closed" }) =>
      adminApi.setProductStatus(id, status),
    onSettled: (_data, _error, { id }) => invalidate(id),
  });
}

export function useChangeUserRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      role,
    }: {
      id: number;
      role: Exclude<Role, "superadmin">;
    }) => adminApi.changeUserRole(id, role),
    onSuccess: (user) =>
      queryClient.setQueryData(queryKeys.user(user.id), user),
  });
}

export function useDeleteUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => usersApi.remove(id),
    onSuccess: (_data, id) =>
      queryClient.removeQueries({ queryKey: queryKeys.user(id) }),
  });
}
