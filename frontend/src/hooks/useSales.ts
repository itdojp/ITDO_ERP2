import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  salesApi,
  SalesQuote,
  SalesOrder,
  Invoice,
  Customer,
  SalesQueryParams,
} from "../services/api/sales";

// Quotes Hooks
export const useQuotes = (params: SalesQueryParams = {}) => {
  return useQuery({
    queryKey: ["sales", "quotes", params],
    queryFn: () => salesApi.getQuotes(params),
    keepPreviousData: true,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useQuote = (id: string) => {
  return useQuery({
    queryKey: ["sales", "quote", id],
    queryFn: () => salesApi.getQuote(id),
    enabled: !!id,
  });
};

export const useCreateQuote = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Parameters<typeof salesApi.createQuote>[0]) =>
      salesApi.createQuote(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sales", "quotes"] });
      queryClient.invalidateQueries({ queryKey: ["sales", "stats"] });
    },
  });
};

export const useUpdateQuote = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<SalesQuote> }) =>
      salesApi.updateQuote(id, data),
    onSuccess: (updatedQuote) => {
      queryClient.invalidateQueries({ queryKey: ["sales", "quotes"] });
      queryClient.setQueryData(
        ["sales", "quote", updatedQuote.id],
        updatedQuote,
      );
    },
  });
};

export const useDeleteQuote = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => salesApi.deleteQuote(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sales", "quotes"] });
    },
  });
};

export const useConvertQuoteToOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (quoteId: string) => salesApi.convertQuoteToOrder(quoteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sales", "quotes"] });
      queryClient.invalidateQueries({ queryKey: ["sales", "orders"] });
      queryClient.invalidateQueries({ queryKey: ["sales", "stats"] });
    },
  });
};

// Orders Hooks
export const useOrders = (params: SalesQueryParams = {}) => {
  return useQuery({
    queryKey: ["sales", "orders", params],
    queryFn: () => salesApi.getOrders(params),
    keepPreviousData: true,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 30 * 1000, // Real-time updates for order processing
  });
};

export const useOrder = (id: string) => {
  return useQuery({
    queryKey: ["sales", "order", id],
    queryFn: () => salesApi.getOrder(id),
    enabled: !!id,
    refetchInterval: 30 * 1000, // Real-time order tracking
  });
};

export const useCreateOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Parameters<typeof salesApi.createOrder>[0]) =>
      salesApi.createOrder(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sales", "orders"] });
      queryClient.invalidateQueries({ queryKey: ["sales", "stats"] });
      queryClient.invalidateQueries({ queryKey: ["inventory"] }); // Update inventory
    },
  });
};

export const useUpdateOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<SalesOrder> }) =>
      salesApi.updateOrder(id, data),
    onSuccess: (updatedOrder) => {
      queryClient.invalidateQueries({ queryKey: ["sales", "orders"] });
      queryClient.setQueryData(
        ["sales", "order", updatedOrder.id],
        updatedOrder,
      );
    },
  });
};

export const useDeleteOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => salesApi.deleteOrder(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sales", "orders"] });
      queryClient.invalidateQueries({ queryKey: ["inventory"] }); // Update inventory
    },
  });
};

export const useFulfillOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      orderId,
      items,
    }: {
      orderId: string;
      items: { item_id: string; quantity: number }[];
    }) => salesApi.fulfillOrder(orderId, items),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sales", "orders"] });
      queryClient.invalidateQueries({ queryKey: ["inventory"] }); // Update inventory
    },
  });
};

// Invoices Hooks
export const useInvoices = (params: SalesQueryParams = {}) => {
  return useQuery({
    queryKey: ["sales", "invoices", params],
    queryFn: () => salesApi.getInvoices(params),
    keepPreviousData: true,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useInvoice = (id: string) => {
  return useQuery({
    queryKey: ["sales", "invoice", id],
    queryFn: () => salesApi.getInvoice(id),
    enabled: !!id,
  });
};

export const useCreateInvoice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Parameters<typeof salesApi.createInvoice>[0]) =>
      salesApi.createInvoice(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sales", "invoices"] });
      queryClient.invalidateQueries({ queryKey: ["sales", "stats"] });
      queryClient.invalidateQueries({ queryKey: ["financial"] }); // Update financials
    },
  });
};

export const useUpdateInvoice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Invoice> }) =>
      salesApi.updateInvoice(id, data),
    onSuccess: (updatedInvoice) => {
      queryClient.invalidateQueries({ queryKey: ["sales", "invoices"] });
      queryClient.setQueryData(
        ["sales", "invoice", updatedInvoice.id],
        updatedInvoice,
      );
    },
  });
};

export const useDeleteInvoice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => salesApi.deleteInvoice(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sales", "invoices"] });
      queryClient.invalidateQueries({ queryKey: ["financial"] }); // Update financials
    },
  });
};

export const useCreateInvoiceFromOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (orderId: string) => salesApi.createInvoiceFromOrder(orderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sales", "invoices"] });
      queryClient.invalidateQueries({ queryKey: ["sales", "orders"] });
      queryClient.invalidateQueries({ queryKey: ["financial"] }); // Update financials
    },
  });
};

export const useRecordPayment = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      invoiceId,
      amount,
      paymentMethod,
      notes,
    }: {
      invoiceId: string;
      amount: number;
      paymentMethod: string;
      notes?: string;
    }) => salesApi.recordPayment(invoiceId, amount, paymentMethod, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sales", "invoices"] });
      queryClient.invalidateQueries({ queryKey: ["financial"] }); // Update financials
    },
  });
};

// Customers Hooks
export const useCustomers = (params: SalesQueryParams = {}) => {
  return useQuery({
    queryKey: ["sales", "customers", params],
    queryFn: () => salesApi.getCustomers(params),
    keepPreviousData: true,
    staleTime: 10 * 60 * 1000, // 10 minutes - customers don't change often
  });
};

export const useCustomer = (id: string) => {
  return useQuery({
    queryKey: ["sales", "customer", id],
    queryFn: () => salesApi.getCustomer(id),
    enabled: !!id,
  });
};

export const useCreateCustomer = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Parameters<typeof salesApi.createCustomer>[0]) =>
      salesApi.createCustomer(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sales", "customers"] });
    },
  });
};

export const useUpdateCustomer = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Customer> }) =>
      salesApi.updateCustomer(id, data),
    onSuccess: (updatedCustomer) => {
      queryClient.invalidateQueries({ queryKey: ["sales", "customers"] });
      queryClient.setQueryData(
        ["sales", "customer", updatedCustomer.id],
        updatedCustomer,
      );
    },
  });
};

export const useDeleteCustomer = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => salesApi.deleteCustomer(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sales", "customers"] });
    },
  });
};

// Analytics & Stats Hooks
export const useSalesStats = () => {
  return useQuery({
    queryKey: ["sales", "stats"],
    queryFn: () => salesApi.getSalesStats(),
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

export const useSalesReport = (
  dateFrom: string,
  dateTo: string,
  groupBy: "day" | "week" | "month",
) => {
  return useQuery({
    queryKey: ["sales", "report", dateFrom, dateTo, groupBy],
    queryFn: () => salesApi.getSalesReport(dateFrom, dateTo, groupBy),
    enabled: !!dateFrom && !!dateTo,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};
