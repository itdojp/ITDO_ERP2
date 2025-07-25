import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  financialApi,
  Account,
  Transaction,
  JournalEntry,
  FinancialReport,
  BudgetPlan,
  TaxReturn,
  FinancialQueryParams,
} from "../services/api/financial";

// Chart of Accounts Hooks
export const useAccounts = (params: FinancialQueryParams = {}) => {
  return useQuery({
    queryKey: ["financial", "accounts", params],
    queryFn: () => financialApi.getAccounts(params),
    keepPreviousData: true,
    staleTime: 10 * 60 * 1000, // 10 minutes - chart of accounts changes infrequently
  });
};

export const useAccount = (id: string) => {
  return useQuery({
    queryKey: ["financial", "account", id],
    queryFn: () => financialApi.getAccount(id),
    enabled: !!id,
  });
};

export const useCreateAccount = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Parameters<typeof financialApi.createAccount>[0]) =>
      financialApi.createAccount(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["financial", "accounts"] });
      queryClient.invalidateQueries({ queryKey: ["financial", "stats"] });
    },
  });
};

export const useUpdateAccount = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Account> }) =>
      financialApi.updateAccount(id, data),
    onSuccess: (updatedAccount) => {
      queryClient.invalidateQueries({ queryKey: ["financial", "accounts"] });
      queryClient.setQueryData(
        ["financial", "account", updatedAccount.id],
        updatedAccount,
      );
    },
  });
};

export const useDeleteAccount = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => financialApi.deleteAccount(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["financial", "accounts"] });
    },
  });
};

// Transactions Hooks
export const useTransactions = (params: FinancialQueryParams = {}) => {
  return useQuery({
    queryKey: ["financial", "transactions", params],
    queryFn: () => financialApi.getTransactions(params),
    keepPreviousData: true,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 60 * 1000, // Refetch every minute for real-time updates
  });
};

export const useTransaction = (id: string) => {
  return useQuery({
    queryKey: ["financial", "transaction", id],
    queryFn: () => financialApi.getTransaction(id),
    enabled: !!id,
  });
};

export const useCreateTransaction = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Parameters<typeof financialApi.createTransaction>[0]) =>
      financialApi.createTransaction(data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["financial", "transactions"],
      });
      queryClient.invalidateQueries({ queryKey: ["financial", "accounts"] });
      queryClient.invalidateQueries({ queryKey: ["financial", "stats"] });
    },
  });
};

export const useUpdateTransaction = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Transaction> }) =>
      financialApi.updateTransaction(id, data),
    onSuccess: (updatedTransaction) => {
      queryClient.invalidateQueries({
        queryKey: ["financial", "transactions"],
      });
      queryClient.setQueryData(
        ["financial", "transaction", updatedTransaction.id],
        updatedTransaction,
      );
      queryClient.invalidateQueries({ queryKey: ["financial", "accounts"] });
    },
  });
};

export const useDeleteTransaction = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => financialApi.deleteTransaction(id),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["financial", "transactions"],
      });
      queryClient.invalidateQueries({ queryKey: ["financial", "accounts"] });
    },
  });
};

export const usePostTransaction = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => financialApi.postTransaction(id),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["financial", "transactions"],
      });
      queryClient.invalidateQueries({ queryKey: ["financial", "accounts"] });
    },
  });
};

// Journal Entries Hooks
export const useJournalEntries = (params: FinancialQueryParams = {}) => {
  return useQuery({
    queryKey: ["financial", "journal-entries", params],
    queryFn: () => financialApi.getJournalEntries(params),
    keepPreviousData: true,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useJournalEntry = (id: string) => {
  return useQuery({
    queryKey: ["financial", "journal-entry", id],
    queryFn: () => financialApi.getJournalEntry(id),
    enabled: !!id,
  });
};

export const useCreateJournalEntry = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Parameters<typeof financialApi.createJournalEntry>[0]) =>
      financialApi.createJournalEntry(data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["financial", "journal-entries"],
      });
      queryClient.invalidateQueries({ queryKey: ["financial", "accounts"] });
    },
  });
};

export const useUpdateJournalEntry = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<JournalEntry> }) =>
      financialApi.updateJournalEntry(id, data),
    onSuccess: (updatedEntry) => {
      queryClient.invalidateQueries({
        queryKey: ["financial", "journal-entries"],
      });
      queryClient.setQueryData(
        ["financial", "journal-entry", updatedEntry.id],
        updatedEntry,
      );
    },
  });
};

export const useDeleteJournalEntry = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => financialApi.deleteJournalEntry(id),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["financial", "journal-entries"],
      });
      queryClient.invalidateQueries({ queryKey: ["financial", "accounts"] });
    },
  });
};

export const usePostJournalEntry = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => financialApi.postJournalEntry(id),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["financial", "journal-entries"],
      });
      queryClient.invalidateQueries({ queryKey: ["financial", "accounts"] });
    },
  });
};

// Financial Reports Hooks
export const useFinancialReports = () => {
  return useQuery({
    queryKey: ["financial", "reports"],
    queryFn: () => financialApi.getReports(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useGenerateReport = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      reportType,
      periodStart,
      periodEnd,
    }: {
      reportType: string;
      periodStart: string;
      periodEnd: string;
    }) => financialApi.generateReport(reportType, periodStart, periodEnd),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["financial", "reports"] });
    },
  });
};

export const useBalanceSheet = (asOfDate: string) => {
  return useQuery({
    queryKey: ["financial", "balance-sheet", asOfDate],
    queryFn: () => financialApi.getBalanceSheet(asOfDate),
    enabled: !!asOfDate,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useIncomeStatement = (periodStart: string, periodEnd: string) => {
  return useQuery({
    queryKey: ["financial", "income-statement", periodStart, periodEnd],
    queryFn: () => financialApi.getIncomeStatement(periodStart, periodEnd),
    enabled: !!periodStart && !!periodEnd,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useCashFlowStatement = (
  periodStart: string,
  periodEnd: string,
) => {
  return useQuery({
    queryKey: ["financial", "cash-flow", periodStart, periodEnd],
    queryFn: () => financialApi.getCashFlowStatement(periodStart, periodEnd),
    enabled: !!periodStart && !!periodEnd,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useTrialBalance = (asOfDate: string) => {
  return useQuery({
    queryKey: ["financial", "trial-balance", asOfDate],
    queryFn: () => financialApi.getTrialBalance(asOfDate),
    enabled: !!asOfDate,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Budget Management Hooks
export const useBudgets = (params: FinancialQueryParams = {}) => {
  return useQuery({
    queryKey: ["financial", "budgets", params],
    queryFn: () => financialApi.getBudgets(params),
    keepPreviousData: true,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useBudget = (id: string) => {
  return useQuery({
    queryKey: ["financial", "budget", id],
    queryFn: () => financialApi.getBudget(id),
    enabled: !!id,
  });
};

export const useCreateBudget = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Parameters<typeof financialApi.createBudget>[0]) =>
      financialApi.createBudget(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["financial", "budgets"] });
    },
  });
};

export const useUpdateBudget = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<BudgetPlan> }) =>
      financialApi.updateBudget(id, data),
    onSuccess: (updatedBudget) => {
      queryClient.invalidateQueries({ queryKey: ["financial", "budgets"] });
      queryClient.setQueryData(
        ["financial", "budget", updatedBudget.id],
        updatedBudget,
      );
    },
  });
};

export const useDeleteBudget = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => financialApi.deleteBudget(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["financial", "budgets"] });
    },
  });
};

// Cash Flow Forecasting Hooks
export const useCashFlowForecasts = () => {
  return useQuery({
    queryKey: ["financial", "cash-flow-forecasts"],
    queryFn: () => financialApi.getCashFlowForecasts(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useCreateCashFlowForecast = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (
      data: Parameters<typeof financialApi.createCashFlowForecast>[0],
    ) => financialApi.createCashFlowForecast(data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["financial", "cash-flow-forecasts"],
      });
    },
  });
};

// Tax Management Hooks
export const useTaxReturns = (params: FinancialQueryParams = {}) => {
  return useQuery({
    queryKey: ["financial", "tax-returns", params],
    queryFn: () => financialApi.getTaxReturns(params),
    keepPreviousData: true,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useTaxReturn = (id: string) => {
  return useQuery({
    queryKey: ["financial", "tax-return", id],
    queryFn: () => financialApi.getTaxReturn(id),
    enabled: !!id,
  });
};

export const useCreateTaxReturn = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Parameters<typeof financialApi.createTaxReturn>[0]) =>
      financialApi.createTaxReturn(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["financial", "tax-returns"] });
    },
  });
};

// Financial Analytics Hooks
export const useFinancialStats = () => {
  return useQuery({
    queryKey: ["financial", "stats"],
    queryFn: () => financialApi.getFinancialStats(),
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

export const useFinancialDashboard = (
  periodStart: string,
  periodEnd: string,
) => {
  return useQuery({
    queryKey: ["financial", "dashboard", periodStart, periodEnd],
    queryFn: () => financialApi.getFinancialDashboard(periodStart, periodEnd),
    enabled: !!periodStart && !!periodEnd,
    refetchInterval: 5 * 60 * 1000, // Real-time dashboard updates
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

export const useAccountBalance = (accountId: string, asOfDate?: string) => {
  return useQuery({
    queryKey: ["financial", "account-balance", accountId, asOfDate],
    queryFn: () => financialApi.getAccountBalance(accountId, asOfDate),
    enabled: !!accountId,
    refetchInterval: 60 * 1000, // Real-time balance updates
    staleTime: 30 * 1000, // 30 seconds
  });
};

export const useReconcileAccount = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      accountId,
      entries,
    }: {
      accountId: string;
      entries: { transaction_id: string; reconciled: boolean }[];
    }) => financialApi.reconcileAccount(accountId, entries),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["financial", "accounts"] });
      queryClient.invalidateQueries({
        queryKey: ["financial", "transactions"],
      });
    },
  });
};
