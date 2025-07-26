import { apiClient } from "./client";

export interface Product {
  id: string;
  sku: string;
  name: string;
  category: string;
  price: number;
  cost: number;
  stock_quantity: number;
  min_stock_level: number;
  status: "active" | "inactive" | "discontinued";
  description?: string;
  supplier_id?: string;
  created_at: string;
  updated_at: string;
}

export interface ProductCreateRequest {
  sku: string;
  name: string;
  category: string;
  price: number;
  cost: number;
  stock_quantity: number;
  min_stock_level: number;
  description?: string;
  supplier_id?: string;
}

export interface ProductUpdateRequest extends Partial<ProductCreateRequest> {
  status?: "active" | "inactive" | "discontinued";
}

export interface ProductsListResponse {
  items: Product[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface ProductsQueryParams {
  page?: number;
  per_page?: number;
  search?: string;
  category?: string;
  status?: "active" | "inactive" | "discontinued";
  min_price?: number;
  max_price?: number;
  low_stock?: boolean;
  sort_by?: "name" | "price" | "stock_quantity" | "created_at";
  sort_order?: "asc" | "desc";
}

export const productsApi = {
  // Get all products with filtering and pagination
  getProducts: async (
    params: ProductsQueryParams = {},
  ): Promise<ProductsListResponse> => {
    const response = await apiClient.get("/api/v1/products", { params });
    return response.data;
  },

  // Get single product by ID
  getProduct: async (id: string): Promise<Product> => {
    const response = await apiClient.get(`/api/v1/products/${id}`);
    return response.data;
  },

  // Create new product
  createProduct: async (data: ProductCreateRequest): Promise<Product> => {
    const response = await apiClient.post("/api/v1/products", data);
    return response.data;
  },

  // Update existing product
  updateProduct: async (
    id: string,
    data: ProductUpdateRequest,
  ): Promise<Product> => {
    const response = await apiClient.put(`/api/v1/products/${id}`, data);
    return response.data;
  },

  // Delete product
  deleteProduct: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/products/${id}`);
  },

  // Bulk operations
  bulkUpdateProducts: async (
    ids: string[],
    data: ProductUpdateRequest,
  ): Promise<Product[]> => {
    const response = await apiClient.patch("/api/v1/products/bulk", {
      product_ids: ids,
      update_data: data,
    });
    return response.data;
  },

  bulkDeleteProducts: async (ids: string[]): Promise<void> => {
    await apiClient.delete("/api/v1/products/bulk", {
      data: { product_ids: ids },
    });
  },

  // Get product categories
  getCategories: async (): Promise<string[]> => {
    const response = await apiClient.get("/api/v1/products/categories");
    return response.data.categories;
  },

  // Stock management
  updateStock: async (
    id: string,
    quantity: number,
    reason?: string,
  ): Promise<Product> => {
    const response = await apiClient.post(`/api/v1/products/${id}/stock`, {
      quantity,
      reason,
    });
    return response.data;
  },

  // Low stock alerts
  getLowStockProducts: async (): Promise<Product[]> => {
    const response = await apiClient.get("/api/v1/products/low-stock");
    return response.data.items;
  },
};
