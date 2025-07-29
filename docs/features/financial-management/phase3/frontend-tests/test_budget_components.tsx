/**
 * 予算管理コンポーネントのテスト
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

// Components
import { BudgetList } from '@/components/financial/budget/BudgetList';
import { BudgetForm } from '@/components/financial/budget/BudgetForm';
import { BudgetDetail } from '@/components/financial/budget/BudgetDetail';
import { BudgetConsumptionChart } from '@/components/financial/budget/BudgetConsumptionChart';
import { BudgetAllocationForm } from '@/components/financial/budget/BudgetAllocationForm';

// Mocks
import { mockBudgets, mockBudgetDetail, mockBudgetConsumption } from '@/test/mocks/budget.mock';
import * as budgetApi from '@/services/api/budget';

// Test utilities
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('BudgetList', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('予算一覧が正しく表示される', async () => {
    vi.spyOn(budgetApi, 'getBudgets').mockResolvedValue({
      data: mockBudgets,
      total: mockBudgets.length,
    });

    render(<BudgetList />, { wrapper: createWrapper() });

    // ローディング状態の確認
    expect(screen.getByTestId('budget-list-loading')).toBeInTheDocument();

    // データ表示の確認
    await waitFor(() => {
      expect(screen.getByText('2024年度全社予算')).toBeInTheDocument();
      expect(screen.getByText('¥500,000,000')).toBeInTheDocument();
      expect(screen.getByText('45.2%')).toBeInTheDocument();
    });

    // 階層表示の確認
    const rows = screen.getAllByRole('row');
    expect(rows).toHaveLength(mockBudgets.length + 1); // ヘッダー行を含む
  });

  it('予算検索が機能する', async () => {
    const mockSearch = vi.spyOn(budgetApi, 'getBudgets').mockResolvedValue({
      data: mockBudgets.filter(b => b.budgetName.includes('営業')),
      total: 1,
    });

    render(<BudgetList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByPlaceholderText('予算名で検索')).toBeInTheDocument();
    });

    // 検索実行
    const searchInput = screen.getByPlaceholderText('予算名で検索');
    await user.type(searchInput, '営業');

    await waitFor(() => {
      expect(mockSearch).toHaveBeenCalledWith(
        expect.objectContaining({
          search: '営業',
        })
      );
    });
  });

  it('新規予算作成ボタンが機能する', async () => {
    const mockNavigate = vi.fn();
    vi.mock('react-router-dom', async () => ({
      ...await vi.importActual('react-router-dom'),
      useNavigate: () => mockNavigate,
    }));

    render(<BudgetList />, { wrapper: createWrapper() });

    const createButton = screen.getByRole('button', { name: '新規予算' });
    await user.click(createButton);

    expect(mockNavigate).toHaveBeenCalledWith('/financial/budgets/new');
  });

  it('予算フィルタリングが機能する', async () => {
    const mockFilter = vi.spyOn(budgetApi, 'getBudgets').mockResolvedValue({
      data: mockBudgets,
      total: mockBudgets.length,
    });

    render(<BudgetList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('combobox', { name: '年度' })).toBeInTheDocument();
    });

    // 年度フィルタ
    const yearSelect = screen.getByRole('combobox', { name: '年度' });
    await user.selectOptions(yearSelect, '2024');

    // ステータスフィルタ
    const statusSelect = screen.getByRole('combobox', { name: 'ステータス' });
    await user.selectOptions(statusSelect, 'approved');

    await waitFor(() => {
      expect(mockFilter).toHaveBeenCalledWith(
        expect.objectContaining({
          fiscalYear: 2024,
          status: 'approved',
        })
      );
    });
  });
});

describe('BudgetForm', () => {
  const user = userEvent.setup();
  const mockOnSubmit = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('新規予算作成フォームが正しくレンダリングされる', () => {
    render(
      <BudgetForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByLabelText('予算コード')).toBeInTheDocument();
    expect(screen.getByLabelText('予算名')).toBeInTheDocument();
    expect(screen.getByLabelText('会計年度')).toBeInTheDocument();
    expect(screen.getByLabelText('予算期間')).toBeInTheDocument();
    expect(screen.getByLabelText('売上予算')).toBeInTheDocument();
    expect(screen.getByLabelText('原価予算')).toBeInTheDocument();
    expect(screen.getByLabelText('経費予算')).toBeInTheDocument();
  });

  it('必須項目の検証が機能する', async () => {
    render(
      <BudgetForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />,
      { wrapper: createWrapper() }
    );

    const submitButton = screen.getByRole('button', { name: '作成' });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('予算コードは必須です')).toBeInTheDocument();
      expect(screen.getByText('予算名は必須です')).toBeInTheDocument();
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });
  });

  it('予算フォームの送信が正しく機能する', async () => {
    render(
      <BudgetForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />,
      { wrapper: createWrapper() }
    );

    // フォーム入力
    await user.type(screen.getByLabelText('予算コード'), 'BUD-2024-001');
    await user.type(screen.getByLabelText('予算名'), 'テスト予算');
    await user.selectOptions(screen.getByLabelText('会計年度'), '2024');
    await user.type(screen.getByLabelText('経費予算'), '1000000');

    const submitButton = screen.getByRole('button', { name: '作成' });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          budgetCode: 'BUD-2024-001',
          budgetName: 'テスト予算',
          fiscalYear: 2024,
          expenseBudget: 1000000,
        })
      );
    });
  });

  it('金額フォーマットが正しく適用される', async () => {
    render(
      <BudgetForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />,
      { wrapper: createWrapper() }
    );

    const expenseInput = screen.getByLabelText('経費予算');
    await user.type(expenseInput, '1000000');

    // フォーカスを外す
    await user.tab();

    await waitFor(() => {
      expect(expenseInput).toHaveValue('¥1,000,000');
    });
  });
});

describe('BudgetDetail', () => {
  const budgetId = 1;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('予算詳細が正しく表示される', async () => {
    vi.spyOn(budgetApi, 'getBudget').mockResolvedValue(mockBudgetDetail);
    vi.spyOn(budgetApi, 'getBudgetConsumption').mockResolvedValue(mockBudgetConsumption);

    render(<BudgetDetail budgetId={budgetId} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('2024年度営業部予算')).toBeInTheDocument();
      expect(screen.getByText('期間: 2024/04/01 - 2025/03/31')).toBeInTheDocument();
      expect(screen.getByText('承認済み')).toBeInTheDocument();
    });

    // タブの確認
    expect(screen.getByRole('tab', { name: '基本情報' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: '費目配分' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: '消化状況' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'アラート' })).toBeInTheDocument();
  });

  it('予算消化グラフが正しく表示される', async () => {
    vi.spyOn(budgetApi, 'getBudget').mockResolvedValue(mockBudgetDetail);
    vi.spyOn(budgetApi, 'getBudgetConsumption').mockResolvedValue(mockBudgetConsumption);

    render(<BudgetDetail budgetId={budgetId} />, { wrapper: createWrapper() });

    // 消化状況タブをクリック
    const consumptionTab = await screen.findByRole('tab', { name: '消化状況' });
    fireEvent.click(consumptionTab);

    await waitFor(() => {
      expect(screen.getByTestId('consumption-chart')).toBeInTheDocument();
      expect(screen.getByText('執行率: 48.5%')).toBeInTheDocument();
      expect(screen.getByText('残額: ¥77,250,000')).toBeInTheDocument();
    });
  });

  it('予算編集ボタンが権限に応じて表示される', async () => {
    const mockBudgetWithPermission = {
      ...mockBudgetDetail,
      canEdit: true,
    };

    vi.spyOn(budgetApi, 'getBudget').mockResolvedValue(mockBudgetWithPermission);

    render(<BudgetDetail budgetId={budgetId} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '編集' })).toBeInTheDocument();
    });
  });
});

describe('BudgetConsumptionChart', () => {
  it('予算消化チャートが正しくレンダリングされる', () => {
    render(
      <BudgetConsumptionChart consumption={mockBudgetConsumption} />,
      { wrapper: createWrapper() }
    );

    // チャート要素の確認
    expect(screen.getByTestId('consumption-chart')).toBeInTheDocument();
    
    // 凡例の確認
    expect(screen.getByText('消化済み')).toBeInTheDocument();
    expect(screen.getByText('残額')).toBeInTheDocument();

    // 費目別の表示確認
    mockBudgetConsumption.allocations.forEach(allocation => {
      expect(screen.getByText(allocation.accountName)).toBeInTheDocument();
    });
  });

  it('アラート閾値が表示される', () => {
    const consumptionWithAlert = {
      ...mockBudgetConsumption,
      consumptionRate: 85.5,
    };

    render(
      <BudgetConsumptionChart consumption={consumptionWithAlert} />,
      { wrapper: createWrapper() }
    );

    // 80%超過の警告表示
    expect(screen.getByTestId('alert-indicator')).toBeInTheDocument();
    expect(screen.getByText('予算の80%を超過しています')).toBeInTheDocument();
  });
});

describe('BudgetAllocationForm', () => {
  const user = userEvent.setup();
  const mockOnSubmit = vi.fn();
  const mockOnCancel = vi.fn();
  const budgetId = 1;
  const totalBudget = 30000000; // 3000万円

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('費目配分フォームが正しくレンダリングされる', () => {
    render(
      <BudgetAllocationForm
        budgetId={budgetId}
        totalBudget={totalBudget}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('費目配分')).toBeInTheDocument();
    expect(screen.getByText('総予算: ¥30,000,000')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '費目を追加' })).toBeInTheDocument();
  });

  it('費目の追加と削除が機能する', async () => {
    render(
      <BudgetAllocationForm
        budgetId={budgetId}
        totalBudget={totalBudget}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />,
      { wrapper: createWrapper() }
    );

    // 初期状態で1行あることを確認
    expect(screen.getAllByRole('row')).toHaveLength(2); // ヘッダー + 1行

    // 費目を追加
    const addButton = screen.getByRole('button', { name: '費目を追加' });
    await user.click(addButton);

    expect(screen.getAllByRole('row')).toHaveLength(3); // ヘッダー + 2行

    // 費目を削除
    const deleteButtons = screen.getAllByRole('button', { name: '削除' });
    await user.click(deleteButtons[0]);

    expect(screen.getAllByRole('row')).toHaveLength(2); // ヘッダー + 1行
  });

  it('配分額の合計検証が機能する', async () => {
    render(
      <BudgetAllocationForm
        budgetId={budgetId}
        totalBudget={totalBudget}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />,
      { wrapper: createWrapper() }
    );

    // 配分額を入力
    const accountSelects = screen.getAllByRole('combobox', { name: '勘定科目' });
    const amountInputs = screen.getAllByRole('textbox', { name: '配分額' });

    await user.selectOptions(accountSelects[0], '7001');
    await user.type(amountInputs[0], '35000000'); // 3500万円（予算超過）

    const submitButton = screen.getByRole('button', { name: '配分実行' });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('配分額の合計が予算総額を超えています')).toBeInTheDocument();
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });
  });

  it('配分率が自動計算される', async () => {
    render(
      <BudgetAllocationForm
        budgetId={budgetId}
        totalBudget={totalBudget}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />,
      { wrapper: createWrapper() }
    );

    const amountInput = screen.getByRole('textbox', { name: '配分額' });
    await user.type(amountInput, '15000000'); // 1500万円

    await waitFor(() => {
      expect(screen.getByText('50.0%')).toBeInTheDocument();
    });
  });
});