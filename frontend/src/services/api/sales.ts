import { apiClient } from './client';

export interface SalesQuote {
  id: string;
  quote_number: string;
  customer_id: string;
  customer_name: string;
  customer_email: string;
  status: 'draft' | 'sent' | 'accepted' | 'rejected' | 'expired';
  valid_until: string;
  subtotal: number;
  tax_amount: number;
  discount_amount: number;
  total_amount: number;
  items: SalesQuoteItem[];
  notes?: string;
  terms_conditions?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface SalesQuoteItem {
  id: string;
  product_id: string;
  product_name: string;
  product_sku: string;
  quantity: number;
  unit_price: number;
  discount_percent: number;
  line_total: number;
}

export interface SalesOrder {
  id: string;
  order_number: string;
  quote_id?: string;
  customer_id: string;
  customer_name: string;
  customer_email: string;
  status: 'pending' | 'confirmed' | 'processing' | 'shipped' | 'delivered' | 'cancelled';
  order_date: string;
  delivery_date?: string;
  subtotal: number;
  tax_amount: number;
  shipping_amount: number;
  discount_amount: number;
  total_amount: number;
  items: SalesOrderItem[];
  shipping_address: Address;
  billing_address: Address;
  payment_status: 'pending' | 'paid' | 'partial' | 'refunded';
  payment_method?: string;
  notes?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface SalesOrderItem {
  id: string;
  product_id: string;
  product_name: string;
  product_sku: string;
  quantity: number;
  unit_price: number;
  discount_percent: number;
  line_total: number;
  fulfilled_quantity: number;
}

export interface Invoice {
  id: string;
  invoice_number: string;
  order_id?: string;
  customer_id: string;
  customer_name: string;
  customer_email: string;
  status: 'draft' | 'sent' | 'paid' | 'partial' | 'overdue' | 'cancelled';
  issue_date: string;
  due_date: string;
  paid_date?: string;
  subtotal: number;
  tax_amount: number;
  discount_amount: number;
  total_amount: number;
  paid_amount: number;
  balance_due: number;
  items: InvoiceItem[];
  billing_address: Address;
  payment_terms?: string;
  notes?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface InvoiceItem {
  id: string;
  product_id: string;
  product_name: string;
  product_sku: string;
  quantity: number;
  unit_price: number;
  discount_percent: number;
  line_total: number;
}

export interface Address {
  street: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
}

export interface Customer {
  id: string;
  name: string;
  email: string;
  phone?: string;
  company?: string;
  billing_address: Address;
  shipping_address?: Address;
  credit_limit?: number;
  payment_terms?: string;
  created_at: string;
  updated_at: string;
}

export interface SalesQueryParams {
  page?: number;
  per_page?: number;
  search?: string;
  status?: string;
  customer_id?: string;
  date_from?: string;
  date_to?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface SalesListResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface SalesStats {
  total_quotes: number;
  total_orders: number;
  total_invoices: number;
  pending_quotes: number;
  pending_orders: number;
  overdue_invoices: number;
  total_revenue: number;
  monthly_revenue: number;
  average_order_value: number;
  top_customers: Customer[];
}

export const salesApi = {
  // Quotes API
  getQuotes: async (params: SalesQueryParams = {}): Promise<SalesListResponse<SalesQuote>> => {
    const response = await apiClient.get('/api/v1/sales/quotes', { params });
    return response.data;
  },

  getQuote: async (id: string): Promise<SalesQuote> => {
    const response = await apiClient.get(`/api/v1/sales/quotes/${id}`);
    return response.data;
  },

  createQuote: async (data: Omit<SalesQuote, 'id' | 'quote_number' | 'created_at' | 'updated_at'>): Promise<SalesQuote> => {
    const response = await apiClient.post('/api/v1/sales/quotes', data);
    return response.data;
  },

  updateQuote: async (id: string, data: Partial<SalesQuote>): Promise<SalesQuote> => {
    const response = await apiClient.put(`/api/v1/sales/quotes/${id}`, data);
    return response.data;
  },

  deleteQuote: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/sales/quotes/${id}`);
  },

  convertQuoteToOrder: async (quoteId: string): Promise<SalesOrder> => {
    const response = await apiClient.post(`/api/v1/sales/quotes/${quoteId}/convert`);
    return response.data;
  },

  // Orders API
  getOrders: async (params: SalesQueryParams = {}): Promise<SalesListResponse<SalesOrder>> => {
    const response = await apiClient.get('/api/v1/sales/orders', { params });
    return response.data;
  },

  getOrder: async (id: string): Promise<SalesOrder> => {
    const response = await apiClient.get(`/api/v1/sales/orders/${id}`);
    return response.data;
  },

  createOrder: async (data: Omit<SalesOrder, 'id' | 'order_number' | 'created_at' | 'updated_at'>): Promise<SalesOrder> => {
    const response = await apiClient.post('/api/v1/sales/orders', data);
    return response.data;
  },

  updateOrder: async (id: string, data: Partial<SalesOrder>): Promise<SalesOrder> => {
    const response = await apiClient.put(`/api/v1/sales/orders/${id}`, data);
    return response.data;
  },

  deleteOrder: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/sales/orders/${id}`);
  },

  fulfillOrder: async (orderId: string, items: { item_id: string; quantity: number }[]): Promise<SalesOrder> => {
    const response = await apiClient.post(`/api/v1/sales/orders/${orderId}/fulfill`, { items });
    return response.data;
  },

  // Invoices API
  getInvoices: async (params: SalesQueryParams = {}): Promise<SalesListResponse<Invoice>> => {
    const response = await apiClient.get('/api/v1/sales/invoices', { params });
    return response.data;
  },

  getInvoice: async (id: string): Promise<Invoice> => {
    const response = await apiClient.get(`/api/v1/sales/invoices/${id}`);
    return response.data;
  },

  createInvoice: async (data: Omit<Invoice, 'id' | 'invoice_number' | 'created_at' | 'updated_at'>): Promise<Invoice> => {
    const response = await apiClient.post('/api/v1/sales/invoices', data);
    return response.data;
  },

  updateInvoice: async (id: string, data: Partial<Invoice>): Promise<Invoice> => {
    const response = await apiClient.put(`/api/v1/sales/invoices/${id}`, data);
    return response.data;
  },

  deleteInvoice: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/sales/invoices/${id}`);
  },

  createInvoiceFromOrder: async (orderId: string): Promise<Invoice> => {
    const response = await apiClient.post(`/api/v1/sales/orders/${orderId}/invoice`);
    return response.data;
  },

  recordPayment: async (invoiceId: string, amount: number, paymentMethod: string, notes?: string): Promise<Invoice> => {
    const response = await apiClient.post(`/api/v1/sales/invoices/${invoiceId}/payment`, {
      amount,
      payment_method: paymentMethod,
      notes,
    });
    return response.data;
  },

  // Customers API
  getCustomers: async (params: SalesQueryParams = {}): Promise<SalesListResponse<Customer>> => {
    const response = await apiClient.get('/api/v1/sales/customers', { params });
    return response.data;
  },

  getCustomer: async (id: string): Promise<Customer> => {
    const response = await apiClient.get(`/api/v1/sales/customers/${id}`);
    return response.data;
  },

  createCustomer: async (data: Omit<Customer, 'id' | 'created_at' | 'updated_at'>): Promise<Customer> => {
    const response = await apiClient.post('/api/v1/sales/customers', data);
    return response.data;
  },

  updateCustomer: async (id: string, data: Partial<Customer>): Promise<Customer> => {
    const response = await apiClient.put(`/api/v1/sales/customers/${id}`, data);
    return response.data;
  },

  deleteCustomer: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/sales/customers/${id}`);
  },

  // Analytics & Stats
  getSalesStats: async (): Promise<SalesStats> => {
    const response = await apiClient.get('/api/v1/sales/stats');
    return response.data;
  },

  getSalesReport: async (dateFrom: string, dateTo: string, groupBy: 'day' | 'week' | 'month'): Promise<any[]> => {
    const response = await apiClient.get('/api/v1/sales/reports', {
      params: { date_from: dateFrom, date_to: dateTo, group_by: groupBy },
    });
    return response.data;
  },
};