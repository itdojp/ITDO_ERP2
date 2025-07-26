import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  productsApi,
  Product,
  ProductsQueryParams,
  ProductCreateRequest,
  ProductUpdateRequest,
} from "../services/api/products";

export const useProducts = (params: ProductsQueryParams = {}) => {
  return useQuery({
    queryKey: ["products", params],
    queryFn: () => productsApi.getProducts(params),
    keepPreviousData: true,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useProduct = (id: string) => {
  return useQuery({
    queryKey: ["product", id],
    queryFn: () => productsApi.getProduct(id),
    enabled: !!id,
  });
};

export const useCreateProduct = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ProductCreateRequest) => productsApi.createProduct(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["products", "categories"] });
    },
  });
};

export const useUpdateProduct = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ProductUpdateRequest }) =>
      productsApi.updateProduct(id, data),
    onSuccess: (updatedProduct) => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.setQueryData(["product", updatedProduct.id], updatedProduct);
    },
  });
};

export const useDeleteProduct = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => productsApi.deleteProduct(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
    },
  });
};

export const useBulkUpdateProducts = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      ids,
      data,
    }: {
      ids: string[];
      data: ProductUpdateRequest;
    }) => productsApi.bulkUpdateProducts(ids, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
    },
  });
};

export const useBulkDeleteProducts = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ids: string[]) => productsApi.bulkDeleteProducts(ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
    },
  });
};

export const useProductCategories = () => {
  return useQuery({
    queryKey: ["products", "categories"],
    queryFn: () => productsApi.getCategories(),
    staleTime: 10 * 60 * 1000, // 10 minutes - categories don't change often
  });
};

export const useLowStockProducts = () => {
  return useQuery({
    queryKey: ["products", "low-stock"],
    queryFn: () => productsApi.getLowStockProducts(),
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });
};

export const useUpdateStock = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      quantity,
      reason,
    }: {
      id: string;
      quantity: number;
      reason?: string;
    }) => productsApi.updateStock(id, quantity, reason),
    onSuccess: (updatedProduct) => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.setQueryData(["product", updatedProduct.id], updatedProduct);
      queryClient.invalidateQueries({ queryKey: ["inventory"] });
    },
  });
};
