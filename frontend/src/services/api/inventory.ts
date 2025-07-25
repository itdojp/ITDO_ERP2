import { apiClient } from "./client";

export interface InventoryItem {
  id: string;
  product_id: string;
  location: string;
  zone: string;
  quantity: number;
  reserved_quantity: number;
  available_quantity: number;
  last_count_date: string;
  status: "available" | "reserved" | "damaged" | "expired";
  created_at: string;
  updated_at: string;
}

export interface InventoryMovement {
  id: string;
  product_id: string;
  location: string;
  movement_type: "in" | "out" | "transfer" | "adjustment";
  quantity: number;
  reference_id?: string;
  reference_type?: "purchase_order" | "sale_order" | "adjustment" | "transfer";
  reason?: string;
  created_by: string;
  created_at: string;
}

export interface StockAdjustment {
  product_id: string;
  location: string;
  quantity_change: number;
  reason: string;
  adjustment_type: "increase" | "decrease" | "count";
}

export interface InventoryTransfer {
  product_id: string;
  from_location: string;
  to_location: string;
  quantity: number;
  reason?: string;
}

export interface InventoryQueryParams {
  page?: number;
  per_page?: number;
  product_id?: string;
  location?: string;
  zone?: string;
  status?: "available" | "reserved" | "damaged" | "expired";
  low_stock?: boolean;
  sort_by?: "quantity" | "last_count_date" | "created_at";
  sort_order?: "asc" | "desc";
}

export interface InventoryListResponse {
  items: InventoryItem[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface MovementsQueryParams {
  page?: number;
  per_page?: number;
  product_id?: string;
  location?: string;
  movement_type?: "in" | "out" | "transfer" | "adjustment";
  date_from?: string;
  date_to?: string;
  sort_by?: "created_at" | "quantity";
  sort_order?: "asc" | "desc";
}

export interface MovementsListResponse {
  items: InventoryMovement[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface InventoryStats {
  total_value: number;
  total_products: number;
  low_stock_count: number;
  out_of_stock_count: number;
  locations_count: number;
  recent_movements: InventoryMovement[];
}

export const inventoryApi = {
  // Get inventory items with filtering
  getInventory: async (
    params: InventoryQueryParams = {},
  ): Promise<InventoryListResponse> => {
    const response = await apiClient.get("/api/v1/inventory", { params });
    return response.data;
  },

  // Get inventory for specific product
  getProductInventory: async (productId: string): Promise<InventoryItem[]> => {
    const response = await apiClient.get(
      `/api/v1/inventory/product/${productId}`,
    );
    return response.data.items;
  },

  // Get inventory movements/history
  getMovements: async (
    params: MovementsQueryParams = {},
  ): Promise<MovementsListResponse> => {
    const response = await apiClient.get("/api/v1/inventory/movements", {
      params,
    });
    return response.data;
  },

  // Stock adjustments
  adjustStock: async (
    adjustment: StockAdjustment,
  ): Promise<InventoryMovement> => {
    const response = await apiClient.post(
      "/api/v1/inventory/adjust",
      adjustment,
    );
    return response.data;
  },

  // Transfer stock between locations
  transferStock: async (
    transfer: InventoryTransfer,
  ): Promise<InventoryMovement> => {
    const response = await apiClient.post(
      "/api/v1/inventory/transfer",
      transfer,
    );
    return response.data;
  },

  // Reserve stock
  reserveStock: async (
    productId: string,
    location: string,
    quantity: number,
  ): Promise<InventoryItem> => {
    const response = await apiClient.post("/api/v1/inventory/reserve", {
      product_id: productId,
      location,
      quantity,
    });
    return response.data;
  },

  // Release reserved stock
  releaseStock: async (
    productId: string,
    location: string,
    quantity: number,
  ): Promise<InventoryItem> => {
    const response = await apiClient.post("/api/v1/inventory/release", {
      product_id: productId,
      location,
      quantity,
    });
    return response.data;
  },

  // Get inventory statistics
  getStats: async (): Promise<InventoryStats> => {
    const response = await apiClient.get("/api/v1/inventory/stats");
    return response.data;
  },

  // Get all locations
  getLocations: async (): Promise<string[]> => {
    const response = await apiClient.get("/api/v1/inventory/locations");
    return response.data.locations;
  },

  // Get zones for a location
  getZones: async (location: string): Promise<string[]> => {
    const response = await apiClient.get(
      `/api/v1/inventory/locations/${location}/zones`,
    );
    return response.data.zones;
  },

  // Physical count update
  updatePhysicalCount: async (
    inventoryId: string,
    actualQuantity: number,
  ): Promise<InventoryItem> => {
    const response = await apiClient.post(
      `/api/v1/inventory/${inventoryId}/count`,
      {
        actual_quantity: actualQuantity,
      },
    );
    return response.data;
  },

  // Get low stock items
  getLowStockItems: async (): Promise<InventoryItem[]> => {
    const response = await apiClient.get("/api/v1/inventory/low-stock");
    return response.data.items;
  },
};
