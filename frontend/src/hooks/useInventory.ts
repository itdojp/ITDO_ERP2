import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  inventoryApi,
  InventoryItem,
  InventoryQueryParams,
  MovementsQueryParams,
  StockAdjustment,
  InventoryTransfer,
} from "../services/api/inventory";

export const useInventory = (params: InventoryQueryParams = {}) => {
  return useQuery({
    queryKey: ["inventory", params],
    queryFn: () => inventoryApi.getInventory(params),
    keepPreviousData: true,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 30 * 1000, // Refetch every 30 seconds for real-time data
  });
};

export const useProductInventory = (productId: string) => {
  return useQuery({
    queryKey: ["inventory", "product", productId],
    queryFn: () => inventoryApi.getProductInventory(productId),
    enabled: !!productId,
    refetchInterval: 30 * 1000, // Real-time updates
  });
};

export const useInventoryMovements = (params: MovementsQueryParams = {}) => {
  return useQuery({
    queryKey: ["inventory", "movements", params],
    queryFn: () => inventoryApi.getMovements(params),
    keepPreviousData: true,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useInventoryStats = () => {
  return useQuery({
    queryKey: ["inventory", "stats"],
    queryFn: () => inventoryApi.getStats(),
    refetchInterval: 2 * 60 * 1000, // Refetch every 2 minutes
  });
};

export const useInventoryLocations = () => {
  return useQuery({
    queryKey: ["inventory", "locations"],
    queryFn: () => inventoryApi.getLocations(),
    staleTime: 10 * 60 * 1000, // 10 minutes - locations don't change often
  });
};

export const useLocationZones = (location: string) => {
  return useQuery({
    queryKey: ["inventory", "zones", location],
    queryFn: () => inventoryApi.getZones(location),
    enabled: !!location,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useLowStockItems = () => {
  return useQuery({
    queryKey: ["inventory", "low-stock"],
    queryFn: () => inventoryApi.getLowStockItems(),
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });
};

export const useAdjustStock = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (adjustment: StockAdjustment) =>
      inventoryApi.adjustStock(adjustment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventory"] });
      queryClient.invalidateQueries({ queryKey: ["products"] });
    },
  });
};

export const useTransferStock = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (transfer: InventoryTransfer) =>
      inventoryApi.transferStock(transfer),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventory"] });
    },
  });
};

export const useReserveStock = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      productId,
      location,
      quantity,
    }: {
      productId: string;
      location: string;
      quantity: number;
    }) => inventoryApi.reserveStock(productId, location, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventory"] });
    },
  });
};

export const useReleaseStock = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      productId,
      location,
      quantity,
    }: {
      productId: string;
      location: string;
      quantity: number;
    }) => inventoryApi.releaseStock(productId, location, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventory"] });
    },
  });
};

export const useUpdatePhysicalCount = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      inventoryId,
      actualQuantity,
    }: {
      inventoryId: string;
      actualQuantity: number;
    }) => inventoryApi.updatePhysicalCount(inventoryId, actualQuantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventory"] });
    },
  });
};
