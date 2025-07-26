import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { apiClient } from "@/services/api";

interface ProductFormData {
  code: string;
  name: string;
  display_name: string;
  sku: string;
  standard_price: number;
  cost_price?: number;
  sale_price?: number;
  status: string;
  product_type: string;
  description?: string;
  category?: string;
  weight?: number;
  length?: number;
  width?: number;
  height?: number;
  barcode?: string;
  supplier?: string;
  lead_time_days?: number;
  minimum_stock_level?: number;
  reorder_point?: number;
  is_active: boolean;
  is_purchasable: boolean;
  is_sellable: boolean;
  is_trackable: boolean;
}

interface Product extends ProductFormData {
  id: number;
  created_at: string;
  updated_at: string;
}

export const ProductForm: React.FC = () => {
  const { productId } = useParams<{ productId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isEditing = !!productId;

  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors, isDirty },
  } = useForm<ProductFormData>({
    defaultValues: {
      status: "active",
      product_type: "product",
      is_active: true,
      is_purchasable: true,
      is_sellable: true,
      is_trackable: true,
    },
  });

  // Fetch product data for editing
  const { data: product, isLoading } = useQuery({
    queryKey: ["product", productId],
    queryFn: async (): Promise<Product> => {
      const response = await apiClient.get(
        `/api/v1/products-basic/${productId}`,
      );
      return response.data;
    },
    enabled: isEditing,
  });

  // Populate form with existing product data
  useEffect(() => {
    if (product && isEditing) {
      reset({
        code: product.code,
        name: product.name,
        display_name: product.display_name,
        sku: product.sku,
        standard_price: product.standard_price,
        cost_price: product.cost_price,
        sale_price: product.sale_price,
        status: product.status,
        product_type: product.product_type,
        description: product.description || "",
        category: product.category || "",
        weight: product.weight,
        barcode: product.barcode || "",
        supplier: product.supplier || "",
        lead_time_days: product.lead_time_days,
        minimum_stock_level: product.minimum_stock_level,
        reorder_point: product.reorder_point,
        is_active: product.is_active,
        is_purchasable: product.is_purchasable,
        is_sellable: product.is_sellable,
        is_trackable: product.is_trackable,
      });
    }
  }, [product, reset, isEditing]);

  // Create mutation
  const createMutation = useMutation({
    mutationFn: async (data: ProductFormData) => {
      const response = await apiClient.post("/api/v1/products-basic", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["product-statistics"] });
      navigate("/products");
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: async (data: ProductFormData) => {
      const response = await apiClient.put(
        `/api/v1/products-basic/${productId}`,
        data,
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["product", productId] });
      queryClient.invalidateQueries({ queryKey: ["product-statistics"] });
      navigate(`/products/${productId}`);
    },
  });

  const onSubmit = async (data: ProductFormData) => {
    setIsSubmitting(true);
    try {
      if (isEditing) {
        await updateMutation.mutateAsync(data);
      } else {
        await createMutation.mutateAsync(data);
      }
    } catch (error) {
      console.error("Error saving product:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    if (isEditing) {
      navigate(`/products/${productId}`);
    } else {
      navigate("/products");
    }
  };

  // Auto-generate display name from name if not provided
  const watchedName = watch("name");
  const watchedDisplayName = watch("display_name");

  useEffect(() => {
    if (watchedName && !watchedDisplayName) {
      setValue("display_name", watchedName, { shouldDirty: true });
    }
  }, [watchedName, watchedDisplayName, setValue]);

  if (isEditing && isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/3"></div>
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {isEditing ? "Edit Product" : "Create New Product"}
          </h1>
          <p className="text-gray-600">
            {isEditing
              ? "Update product information"
              : "Add a new product to your catalog"}
          </p>
        </div>
        <button
          onClick={handleCancel}
          className="text-gray-400 hover:text-gray-600"
          title="Cancel"
        >
          <svg
            className="h-6 w-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Basic Information */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Basic Information</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label
                    htmlFor="code"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Product Code *
                  </label>
                  <input
                    type="text"
                    id="code"
                    {...register("code", {
                      required: "Product code is required",
                      pattern: {
                        value: /^[A-Z0-9_-]+$/,
                        message:
                          "Code must contain only uppercase letters, numbers, hyphens, and underscores",
                      },
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., PROD001"
                  />
                  {errors.code && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.code.message}
                    </p>
                  )}
                </div>

                <div>
                  <label
                    htmlFor="sku"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    SKU *
                  </label>
                  <input
                    type="text"
                    id="sku"
                    {...register("sku", { required: "SKU is required" })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Stock Keeping Unit"
                  />
                  {errors.sku && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.sku.message}
                    </p>
                  )}
                </div>

                <div className="md:col-span-2">
                  <label
                    htmlFor="name"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Product Name *
                  </label>
                  <input
                    type="text"
                    id="name"
                    {...register("name", {
                      required: "Product name is required",
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter product name"
                  />
                  {errors.name && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.name.message}
                    </p>
                  )}
                </div>

                <div className="md:col-span-2">
                  <label
                    htmlFor="display_name"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Display Name
                  </label>
                  <input
                    type="text"
                    id="display_name"
                    {...register("display_name")}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Display name (defaults to product name)"
                  />
                </div>

                <div>
                  <label
                    htmlFor="category"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Category
                  </label>
                  <input
                    type="text"
                    id="category"
                    {...register("category")}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Product category"
                  />
                </div>

                <div>
                  <label
                    htmlFor="barcode"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Barcode
                  </label>
                  <input
                    type="text"
                    id="barcode"
                    {...register("barcode")}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Product barcode"
                  />
                </div>

                <div className="md:col-span-2">
                  <label
                    htmlFor="description"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Description
                  </label>
                  <textarea
                    id="description"
                    rows={3}
                    {...register("description")}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Product description"
                  />
                </div>
              </div>
            </div>

            {/* Pricing */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Pricing</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label
                    htmlFor="standard_price"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Standard Price *
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-2 text-gray-500">
                      $
                    </span>
                    <input
                      type="number"
                      step="0.01"
                      id="standard_price"
                      {...register("standard_price", {
                        required: "Standard price is required",
                        min: { value: 0, message: "Price must be positive" },
                      })}
                      className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="0.00"
                    />
                  </div>
                  {errors.standard_price && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.standard_price.message}
                    </p>
                  )}
                </div>

                <div>
                  <label
                    htmlFor="cost_price"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Cost Price
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-2 text-gray-500">
                      $
                    </span>
                    <input
                      type="number"
                      step="0.01"
                      id="cost_price"
                      {...register("cost_price", {
                        min: {
                          value: 0,
                          message: "Cost price must be positive",
                        },
                      })}
                      className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="0.00"
                    />
                  </div>
                  {errors.cost_price && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.cost_price.message}
                    </p>
                  )}
                </div>

                <div>
                  <label
                    htmlFor="sale_price"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Sale Price
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-2 text-gray-500">
                      $
                    </span>
                    <input
                      type="number"
                      step="0.01"
                      id="sale_price"
                      {...register("sale_price", {
                        min: {
                          value: 0,
                          message: "Sale price must be positive",
                        },
                      })}
                      className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="0.00"
                    />
                  </div>
                  {errors.sale_price && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.sale_price.message}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Physical Properties */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">
                Physical Properties
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label
                    htmlFor="weight"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Weight (kg)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    id="weight"
                    {...register("weight", {
                      min: { value: 0, message: "Weight must be positive" },
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0.00"
                  />
                  {errors.weight && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.weight.message}
                    </p>
                  )}
                </div>

                <div>
                  <label
                    htmlFor="length"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Length (cm)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    id="length"
                    {...register("length", {
                      min: { value: 0, message: "Length must be positive" },
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0.00"
                  />
                  {errors.length && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.length.message}
                    </p>
                  )}
                </div>

                <div>
                  <label
                    htmlFor="width"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Width (cm)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    id="width"
                    {...register("width", {
                      min: { value: 0, message: "Width must be positive" },
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0.00"
                  />
                  {errors.width && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.width.message}
                    </p>
                  )}
                </div>

                <div>
                  <label
                    htmlFor="height"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Height (cm)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    id="height"
                    {...register("height", {
                      min: { value: 0, message: "Height must be positive" },
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0.00"
                  />
                  {errors.height && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.height.message}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Status & Type */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Status & Type</h2>
              <div className="space-y-4">
                <div>
                  <label
                    htmlFor="status"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Status
                  </label>
                  <select
                    id="status"
                    {...register("status", { required: "Status is required" })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                    <option value="discontinued">Discontinued</option>
                  </select>
                  {errors.status && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.status.message}
                    </p>
                  )}
                </div>

                <div>
                  <label
                    htmlFor="product_type"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Product Type
                  </label>
                  <select
                    id="product_type"
                    {...register("product_type", {
                      required: "Product type is required",
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="product">Product</option>
                    <option value="service">Service</option>
                    <option value="kit">Kit</option>
                  </select>
                  {errors.product_type && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.product_type.message}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Inventory Settings */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Inventory</h2>
              <div className="space-y-4">
                <div>
                  <label
                    htmlFor="supplier"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Supplier
                  </label>
                  <input
                    type="text"
                    id="supplier"
                    {...register("supplier")}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Supplier name"
                  />
                </div>

                <div>
                  <label
                    htmlFor="lead_time_days"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Lead Time (days)
                  </label>
                  <input
                    type="number"
                    id="lead_time_days"
                    {...register("lead_time_days", {
                      min: { value: 0, message: "Lead time must be positive" },
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0"
                  />
                  {errors.lead_time_days && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.lead_time_days.message}
                    </p>
                  )}
                </div>

                <div>
                  <label
                    htmlFor="minimum_stock_level"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Minimum Stock Level
                  </label>
                  <input
                    type="number"
                    id="minimum_stock_level"
                    {...register("minimum_stock_level", {
                      min: {
                        value: 0,
                        message: "Minimum stock level must be positive",
                      },
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0"
                  />
                  {errors.minimum_stock_level && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.minimum_stock_level.message}
                    </p>
                  )}
                </div>

                <div>
                  <label
                    htmlFor="reorder_point"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Reorder Point
                  </label>
                  <input
                    type="number"
                    id="reorder_point"
                    {...register("reorder_point", {
                      min: {
                        value: 0,
                        message: "Reorder point must be positive",
                      },
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0"
                  />
                  {errors.reorder_point && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.reorder_point.message}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Capabilities */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Capabilities</h2>
              <div className="space-y-4">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_active"
                    {...register("is_active")}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label
                    htmlFor="is_active"
                    className="ml-2 block text-sm text-gray-900"
                  >
                    Active
                  </label>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_purchasable"
                    {...register("is_purchasable")}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label
                    htmlFor="is_purchasable"
                    className="ml-2 block text-sm text-gray-900"
                  >
                    Can be purchased
                  </label>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_sellable"
                    {...register("is_sellable")}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label
                    htmlFor="is_sellable"
                    className="ml-2 block text-sm text-gray-900"
                  >
                    Can be sold
                  </label>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_trackable"
                    {...register("is_trackable")}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label
                    htmlFor="is_trackable"
                    className="ml-2 block text-sm text-gray-900"
                  >
                    Track inventory
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Form Actions */}
        <div className="flex justify-end space-x-4 pt-6 border-t">
          <button
            type="button"
            onClick={handleCancel}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting || !isDirty}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                {isEditing ? "Updating..." : "Creating..."}
              </div>
            ) : (
              <>{isEditing ? "Update Product" : "Create Product"}</>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ProductForm;
