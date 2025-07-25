import { apiClient } from './client';

export interface Account {
  id: string;
  account_code: string;
  account_name: string;
  account_type: 'asset' | 'liability' | 'equity' | 'revenue' | 'expense';
  parent_account_id?: string;
  is_active: boolean;
  balance: number;
  currency: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface Transaction {
  id: string;
  transaction_number: string;
  transaction_date: string;
  description: string;
  reference?: string;
  total_amount: number;
  currency: string;
  entries: TransactionEntry[];
  status: 'draft' | 'posted' | 'reconciled';
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface TransactionEntry {
  id: string;
  account_id: string;
  account_code: string;
  account_name: string;
  debit_amount: number;
  credit_amount: number;
  description?: string;
}

export interface JournalEntry {
  id: string;
  entry_number: string;
  entry_date: string;
  description: string;
  reference?: string;
  total_debits: number;
  total_credits: number;
  entries: JournalEntryLine[];
  status: 'draft' | 'posted';
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface JournalEntryLine {
  id: string;
  account_id: string;
  account_code: string;
  account_name: string;
  description?: string;
  debit_amount: number;
  credit_amount: number;
}

export interface FinancialReport {
  id: string;
  report_type: 'balance_sheet' | 'income_statement' | 'cash_flow' | 'trial_balance';
  report_name: string;
  period_start: string;
  period_end: string;
  data: FinancialReportData[];
  total_assets?: number;
  total_liabilities?: number;
  total_equity?: number;
  net_income?: number;
  generated_at: string;
}

export interface FinancialReportData {
  account_code: string;
  account_name: string;
  account_type: string;
  balance: number;
  previous_balance?: number;
  variance?: number;
  percentage?: number;
  children?: FinancialReportData[];
}

export interface BudgetPlan {
  id: string;
  budget_name: string;
  fiscal_year: string;
  period_start: string;
  period_end: string;
  status: 'draft' | 'approved' | 'active' | 'closed';
  budget_items: BudgetItem[];
  total_revenue_budget: number;
  total_expense_budget: number;
  net_budget: number;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface BudgetItem {
  id: string;
  account_id: string;
  account_code: string;
  account_name: string;
  budgeted_amount: number;
  actual_amount: number;
  variance: number;
  variance_percentage: number;
  period_breakdown: MonthlyBudget[];
}

export interface MonthlyBudget {
  month: number;
  budgeted_amount: number;
  actual_amount: number;
  variance: number;
}

export interface CashFlowForecast {
  id: string;
  forecast_name: string;
  period_start: string;
  period_end: string;
  opening_balance: number;
  closing_balance: number;
  cash_flows: CashFlowItem[];
  created_at: string;
  updated_at: string;
}

export interface CashFlowItem {
  date: string;
  description: string;
  category: 'operating' | 'investing' | 'financing';
  cash_in: number;
  cash_out: number;
  net_flow: number;
  running_balance: number;
}

export interface TaxReturn {
  id: string;
  tax_year: string;
  return_type: 'corporate' | 'sales' | 'payroll' | 'property';
  status: 'draft' | 'filed' | 'accepted' | 'amended';
  due_date: string;
  filed_date?: string;
  tax_liability: number;
  tax_paid: number;
  balance_due: number;
  refund_amount: number;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface FinancialQueryParams {
  page?: number;
  per_page?: number;
  search?: string;
  account_type?: string;
  date_from?: string;
  date_to?: string;
  status?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface FinancialListResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface FinancialStats {
  total_assets: number;
  total_liabilities: number;
  total_equity: number;
  total_revenue: number;
  total_expenses: number;
  net_income: number;
  cash_balance: number;
  accounts_receivable: number;
  accounts_payable: number;
  monthly_revenue: number[];
  monthly_expenses: number[];
  profit_margin: number;
  current_ratio: number;
  debt_to_equity: number;
}

export const financialApi = {
  // Chart of Accounts
  getAccounts: async (params: FinancialQueryParams = {}): Promise<FinancialListResponse<Account>> => {
    const response = await apiClient.get('/api/v1/financial/accounts', { params });
    return response.data;
  },

  getAccount: async (id: string): Promise<Account> => {
    const response = await apiClient.get(`/api/v1/financial/accounts/${id}`);
    return response.data;
  },

  createAccount: async (data: Omit<Account, 'id' | 'balance' | 'created_at' | 'updated_at'>): Promise<Account> => {
    const response = await apiClient.post('/api/v1/financial/accounts', data);
    return response.data;
  },

  updateAccount: async (id: string, data: Partial<Account>): Promise<Account> => {
    const response = await apiClient.put(`/api/v1/financial/accounts/${id}`, data);
    return response.data;
  },

  deleteAccount: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/financial/accounts/${id}`);
  },

  // Transactions
  getTransactions: async (params: FinancialQueryParams = {}): Promise<FinancialListResponse<Transaction>> => {
    const response = await apiClient.get('/api/v1/financial/transactions', { params });
    return response.data;
  },

  getTransaction: async (id: string): Promise<Transaction> => {
    const response = await apiClient.get(`/api/v1/financial/transactions/${id}`);
    return response.data;
  },

  createTransaction: async (data: Omit<Transaction, 'id' | 'transaction_number' | 'created_at' | 'updated_at'>): Promise<Transaction> => {
    const response = await apiClient.post('/api/v1/financial/transactions', data);
    return response.data;
  },

  updateTransaction: async (id: string, data: Partial<Transaction>): Promise<Transaction> => {
    const response = await apiClient.put(`/api/v1/financial/transactions/${id}`, data);
    return response.data;
  },

  deleteTransaction: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/financial/transactions/${id}`);
  },

  postTransaction: async (id: string): Promise<Transaction> => {
    const response = await apiClient.post(`/api/v1/financial/transactions/${id}/post`);
    return response.data;
  },

  // Journal Entries
  getJournalEntries: async (params: FinancialQueryParams = {}): Promise<FinancialListResponse<JournalEntry>> => {
    const response = await apiClient.get('/api/v1/financial/journal-entries', { params });
    return response.data;
  },

  getJournalEntry: async (id: string): Promise<JournalEntry> => {
    const response = await apiClient.get(`/api/v1/financial/journal-entries/${id}`);
    return response.data;
  },

  createJournalEntry: async (data: Omit<JournalEntry, 'id' | 'entry_number' | 'total_debits' | 'total_credits' | 'created_at' | 'updated_at'>): Promise<JournalEntry> => {
    const response = await apiClient.post('/api/v1/financial/journal-entries', data);
    return response.data;
  },

  updateJournalEntry: async (id: string, data: Partial<JournalEntry>): Promise<JournalEntry> => {
    const response = await apiClient.put(`/api/v1/financial/journal-entries/${id}`, data);
    return response.data;
  },

  deleteJournalEntry: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/financial/journal-entries/${id}`);
  },

  postJournalEntry: async (id: string): Promise<JournalEntry> => {
    const response = await apiClient.post(`/api/v1/financial/journal-entries/${id}/post`);
    return response.data;
  },

  // Financial Reports
  getReports: async (): Promise<FinancialReport[]> => {
    const response = await apiClient.get('/api/v1/financial/reports');
    return response.data;
  },

  generateReport: async (reportType: string, periodStart: string, periodEnd: string): Promise<FinancialReport> => {
    const response = await apiClient.post('/api/v1/financial/reports/generate', {
      report_type: reportType,
      period_start: periodStart,
      period_end: periodEnd,
    });
    return response.data;
  },

  getBalanceSheet: async (asOfDate: string): Promise<FinancialReport> => {
    const response = await apiClient.get('/api/v1/financial/reports/balance-sheet', {
      params: { as_of_date: asOfDate },
    });
    return response.data;
  },

  getIncomeStatement: async (periodStart: string, periodEnd: string): Promise<FinancialReport> => {
    const response = await apiClient.get('/api/v1/financial/reports/income-statement', {
      params: { period_start: periodStart, period_end: periodEnd },
    });
    return response.data;
  },

  getCashFlowStatement: async (periodStart: string, periodEnd: string): Promise<FinancialReport> => {
    const response = await apiClient.get('/api/v1/financial/reports/cash-flow', {
      params: { period_start: periodStart, period_end: periodEnd },
    });
    return response.data;
  },

  getTrialBalance: async (asOfDate: string): Promise<FinancialReport> => {
    const response = await apiClient.get('/api/v1/financial/reports/trial-balance', {
      params: { as_of_date: asOfDate },
    });
    return response.data;
  },

  // Budget Management
  getBudgets: async (params: FinancialQueryParams = {}): Promise<FinancialListResponse<BudgetPlan>> => {
    const response = await apiClient.get('/api/v1/financial/budgets', { params });
    return response.data;
  },

  getBudget: async (id: string): Promise<BudgetPlan> => {
    const response = await apiClient.get(`/api/v1/financial/budgets/${id}`);
    return response.data;
  },

  createBudget: async (data: Omit<BudgetPlan, 'id' | 'total_revenue_budget' | 'total_expense_budget' | 'net_budget' | 'created_at' | 'updated_at'>): Promise<BudgetPlan> => {
    const response = await apiClient.post('/api/v1/financial/budgets', data);
    return response.data;
  },

  updateBudget: async (id: string, data: Partial<BudgetPlan>): Promise<BudgetPlan> => {
    const response = await apiClient.put(`/api/v1/financial/budgets/${id}`, data);
    return response.data;
  },

  deleteBudget: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/financial/budgets/${id}`);
  },

  // Cash Flow Forecasting
  getCashFlowForecasts: async (): Promise<CashFlowForecast[]> => {
    const response = await apiClient.get('/api/v1/financial/cash-flow-forecasts');
    return response.data;
  },

  createCashFlowForecast: async (data: Omit<CashFlowForecast, 'id' | 'closing_balance' | 'created_at' | 'updated_at'>): Promise<CashFlowForecast> => {
    const response = await apiClient.post('/api/v1/financial/cash-flow-forecasts', data);
    return response.data;
  },

  // Tax Management
  getTaxReturns: async (params: FinancialQueryParams = {}): Promise<FinancialListResponse<TaxReturn>> => {
    const response = await apiClient.get('/api/v1/financial/tax-returns', { params });
    return response.data;
  },

  getTaxReturn: async (id: string): Promise<TaxReturn> => {
    const response = await apiClient.get(`/api/v1/financial/tax-returns/${id}`);
    return response.data;
  },

  createTaxReturn: async (data: Omit<TaxReturn, 'id' | 'created_at' | 'updated_at'>): Promise<TaxReturn> => {
    const response = await apiClient.post('/api/v1/financial/tax-returns', data);
    return response.data;
  },

  // Financial Analytics
  getFinancialStats: async (): Promise<FinancialStats> => {
    const response = await apiClient.get('/api/v1/financial/stats');
    return response.data;
  },

  getFinancialDashboard: async (periodStart: string, periodEnd: string): Promise<any> => {
    const response = await apiClient.get('/api/v1/financial/dashboard', {
      params: { period_start: periodStart, period_end: periodEnd },
    });
    return response.data;
  },

  getAccountBalance: async (accountId: string, asOfDate?: string): Promise<{ balance: number; currency: string }> => {
    const response = await apiClient.get(`/api/v1/financial/accounts/${accountId}/balance`, {
      params: asOfDate ? { as_of_date: asOfDate } : {},
    });
    return response.data;
  },

  reconcileAccount: async (accountId: string, entries: { transaction_id: string; reconciled: boolean }[]): Promise<void> => {
    await apiClient.post(`/api/v1/financial/accounts/${accountId}/reconcile`, { entries });
  },
};