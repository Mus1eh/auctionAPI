import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { adminApi, bidsApi, PAGE_SIZE, productsApi, usersApi } from "./endpoints";
import type {
  BidDecision,
  ProductCreate,
  ProductPatch,
  ProductStatus,
  Role,
} from "./types";
import { isPrivateStatus } from "./types";

export const queryKeys = {
  products: ["products"] as const,
  // Private statuses hold the signed-in user's own products, so they live under
  // the per-user "my-products" root and are dropped on sign-out.
  productsByStatus: (status: ProductStatus, page = 1) =>
    isPrivateStatus(status)
      ? (["my-products", "status", status, page] as const)
      : (["products", "status", status, page] as const),
  product: (id: number) => ["products", "detail", id] as const,
  myProducts: ["my-products"] as const,
  myProductsPage: (page: number) => ["my-products", "mine", page] as const,
  me: ["users", "me"] as const,
  bids: (productId: number) => ["bids", productId] as const,
  bidsPage: (productId: number, page: number) =>
    ["bids", productId, page] as const,
  adminProducts: ["admin", "products"] as const,
  adminProductsByStatus: (status: ProductStatus, page = 1, limit = PAGE_SIZE) =>
    ["admin", "products", status, page, limit] as const,
  pendingRequests: ["admin", "pending-requests"] as const,
  pendingRequestsPage: (page: number, limit: number) =>
    ["admin", "pending-requests", page, limit] as const,
  adminDashboard: ["admin", "dashboard"] as const,
  user: (id: number) => ["users", id] as const,
};

/** Query roots holding per-user data; dropped from the cache on sign-out.
 * "products" is included because product details can be the user's private drafts. */
export const PRIVATE_QUERY_ROOTS = ["my-products", "admin", "users", "products"];

/** The API has no push channel; active auctions are polled (as suggested in app/routers/bids.py). */
export const LIVE_POLL_MS = 3000;

export function useProductsByStatus(status: ProductStatus, page = 1) {
  return useQuery({
    queryKey: queryKeys.productsByStatus(status, page),
    queryFn: () => productsApi.listByStatus(status, page),
    placeholderData: keepPreviousData,
    refetchInterval: status === "active" ? LIVE_POLL_MS * 3 : false,
  });
}

/** Admin view: every user's products, including private draft/closed ones. */
export function useAdminProductsByStatus(
  status: ProductStatus,
  page = 1,
  limit = PAGE_SIZE,
) {
  return useQuery({
    queryKey: queryKeys.adminProductsByStatus(status, page, limit),
    queryFn: () => adminApi.productsByStatus(status, page, limit),
    placeholderData: keepPreviousData,
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

export function useMyProducts(page = 1, enabled = true) {
  return useQuery({
    queryKey: queryKeys.myProductsPage(page),
    queryFn: () => productsApi.mine(page),
    placeholderData: keepPreviousData,
    enabled,
  });
}

/** The signed-in user; its id decides whether a product is the user's own. */
export function useMe(enabled = true) {
  return useQuery({
    queryKey: queryKeys.me,
    queryFn: usersApi.me,
    enabled,
    staleTime: 5 * 60 * 1000,
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

export function usePendingRequests(page = 1, limit = PAGE_SIZE) {
  return useQuery({
    queryKey: queryKeys.pendingRequestsPage(page, limit),
    queryFn: () => adminApi.pendingRequests(page, limit),
    placeholderData: keepPreviousData,
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
      queryClient.invalidateQueries({ queryKey: queryKeys.adminProducts }),
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
