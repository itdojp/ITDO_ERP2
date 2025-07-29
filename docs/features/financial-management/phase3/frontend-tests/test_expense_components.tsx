/**
 * 経費管理コンポーネントのテスト
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';

// Components
import { ExpenseForm } from '@/components/financial/expense/ExpenseForm';
import { ExpenseList } from '@/components/financial/expense/ExpenseList';
import { ExpenseApprovalList } from '@/components/financial/expense/ExpenseApprovalList';
import { ExpenseDetail } from '@/components/financial/expense/ExpenseDetail';
import { ReceiptUpload } from '@/components/financial/expense/ReceiptUpload';
import { ExpenseOCR } from '@/components/financial/expense/ExpenseOCR';

// Mocks
import { mockExpenses, mockExpenseDetail, mockPendingApprovals } from '@/test/mocks/expense.mock';
import * as expenseApi from '@/services/api/expense';

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

describe('ExpenseForm', () => {
  const user = userEvent.setup();
  const mockOnSubmit = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('経費申請フォームが正しくレンダリングされる', () => {
    render(
      <ExpenseForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByLabelText('日付')).toBeInTheDocument();
    expect(screen.getByLabelText('部門')).toBeInTheDocument();
    expect(screen.getByLabelText('プロジェクト')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '明細を追加' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '申請' })).toBeInTheDocument();
  });

  it('経費明細の追加と削除が機能する', async () => {
    render(
      <ExpenseForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />,
      { wrapper: createWrapper() }
    );

    // 初期状態で1つの明細行があることを確認
    expect(screen.getAllByTestId('expense-item-row')).toHaveLength(1);

    // 明細を追加
    const addButton = screen.getByRole('button', { name: '明細を追加' });
    await user.click(addButton);

    expect(screen.getAllByTestId('expense-item-row')).toHaveLength(2);

    // 明細を削除
    const deleteButtons = screen.getAllByRole('button', { name: '削除' });
    await user.click(deleteButtons[0]);

    await waitFor(() => {
      expect(screen.getAllByTestId('expense-item-row')).toHaveLength(1);
    });
  });

  it('金額計算が正しく行われる', async () => {
    render(
      <ExpenseForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />,
      { wrapper: createWrapper() }
    );

    // 経費明細を入力
    const amountInput = screen.getByLabelText('金額');
    const taxRateSelect = screen.getByLabelText('税率');

    await user.type(amountInput, '10000');
    await user.selectOptions(taxRateSelect, '10');

    await waitFor(() => {
      expect(screen.getByTestId('subtotal').textContent).toBe('¥10,000');
      expect(screen.getByTestId('tax-amount').textContent).toBe('¥1,000');
      expect(screen.getByTestId('total-amount').textContent).toBe('¥11,000');
    });
  });

  it('領収書アップロードが機能する', async () => {
    const mockFile = new File(['receipt'], 'receipt.jpg', { type: 'image/jpeg' });
    
    render(
      <ExpenseForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />,
      { wrapper: createWrapper() }
    );

    const fileInput = screen.getByLabelText('領収書をアップロード');
    await user.upload(fileInput, mockFile);

    await waitFor(() => {
      expect(screen.getByText('receipt.jpg')).toBeInTheDocument();
      expect(screen.getByAltText('領収書プレビュー')).toBeInTheDocument();
    });
  });

  it('フォーム送信時の検証が機能する', async () => {
    render(
      <ExpenseForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />,
      { wrapper: createWrapper() }
    );

    // 必須項目を入力せずに送信
    const submitButton = screen.getByRole('button', { name: '申請' });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('経費種別を選択してください')).toBeInTheDocument();
      expect(screen.getByText('金額を入力してください')).toBeInTheDocument();
      expect(screen.getByText('内容を入力してください')).toBeInTheDocument();
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });
  });

  it('下書き保存が機能する', async () => {
    const mockSaveDraft = vi.fn();
    
    render(
      <ExpenseForm 
        onSubmit={mockOnSubmit} 
        onCancel={mockOnCancel}
        onSaveDraft={mockSaveDraft}
      />,
      { wrapper: createWrapper() }
    );

    // 一部のデータを入力
    await user.type(screen.getByLabelText('金額'), '5000');
    await user.type(screen.getByLabelText('内容'), 'タクシー代');

    // 下書き保存
    const draftButton = screen.getByRole('button', { name: '下書き保存' });
    await user.click(draftButton);

    await waitFor(() => {
      expect(mockSaveDraft).toHaveBeenCalledWith(
        expect.objectContaining({
          items: expect.arrayContaining([
            expect.objectContaining({
              amount: 5000,
              description: 'タクシー代',
            })
          ])
        })
      );
    });
  });
});

describe('ExpenseList', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('経費一覧が正しく表示される', async () => {
    vi.spyOn(expenseApi, 'getExpenses').mockResolvedValue({
      data: mockExpenses,
      total: mockExpenses.length,
    });

    render(<ExpenseList />, { wrapper: createWrapper() });

    await waitFor(() => {
      mockExpenses.forEach(expense => {
        expect(screen.getByText(expense.expenseNumber)).toBeInTheDocument();
        expect(screen.getByText(`¥${expense.totalAmount.toLocaleString()}`)).toBeInTheDocument();
      });
    });
  });

  it('ステータスフィルタが機能する', async () => {
    const mockGetExpenses = vi.spyOn(expenseApi, 'getExpenses').mockResolvedValue({
      data: mockExpenses,
      total: mockExpenses.length,
    });

    render(<ExpenseList />, { wrapper: createWrapper() });

    const statusFilter = screen.getByRole('combobox', { name: 'ステータス' });
    await user.selectOptions(statusFilter, 'pending');

    await waitFor(() => {
      expect(mockGetExpenses).toHaveBeenCalledWith(
        expect.objectContaining({
          status: 'pending',
        })
      );
    });
  });

  it('期間フィルタが機能する', async () => {
    const mockGetExpenses = vi.spyOn(expenseApi, 'getExpenses').mockResolvedValue({
      data: mockExpenses,
      total: mockExpenses.length,
    });

    render(<ExpenseList />, { wrapper: createWrapper() });

    // 開始日を設定
    const startDateInput = screen.getByLabelText('開始日');
    await user.type(startDateInput, '2024-07-01');

    // 終了日を設定
    const endDateInput = screen.getByLabelText('終了日');
    await user.type(endDateInput, '2024-07-31');

    await waitFor(() => {
      expect(mockGetExpenses).toHaveBeenCalledWith(
        expect.objectContaining({
          startDate: '2024-07-01',
          endDate: '2024-07-31',
        })
      );
    });
  });

  it('一括選択と操作が機能する', async () => {
    vi.spyOn(expenseApi, 'getExpenses').mockResolvedValue({
      data: mockExpenses.filter(e => e.status === 'draft'),
      total: 2,
    });

    render(<ExpenseList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('checkbox', { name: 'すべて選択' })).toBeInTheDocument();
    });

    // すべて選択
    const selectAllCheckbox = screen.getByRole('checkbox', { name: 'すべて選択' });
    await user.click(selectAllCheckbox);

    // 一括削除ボタンが表示される
    expect(screen.getByRole('button', { name: '一括削除' })).toBeInTheDocument();
  });
});

describe('ExpenseApprovalList', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('承認待ち一覧が正しく表示される', async () => {
    vi.spyOn(expenseApi, 'getPendingApprovals').mockResolvedValue({
      data: mockPendingApprovals,
      total: mockPendingApprovals.length,
    });

    render(<ExpenseApprovalList />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('承認待ち経費')).toBeInTheDocument();
      expect(screen.getByTestId('pending-count').textContent).toBe('12');
      
      mockPendingApprovals.forEach(expense => {
        expect(screen.getByText(expense.employeeName)).toBeInTheDocument();
      });
    });
  });

  it('個別承認が機能する', async () => {
    vi.spyOn(expenseApi, 'getPendingApprovals').mockResolvedValue({
      data: mockPendingApprovals,
      total: mockPendingApprovals.length,
    });

    const mockApprove = vi.spyOn(expenseApi, 'approveExpense').mockResolvedValue({
      success: true,
    });

    render(<ExpenseApprovalList />, { wrapper: createWrapper() });

    await waitFor(() => {
      const approveButtons = screen.getAllByRole('button', { name: '承認' });
      expect(approveButtons.length).toBeGreaterThan(0);
    });

    const firstApproveButton = screen.getAllByRole('button', { name: '承認' })[0];
    await user.click(firstApproveButton);

    // 確認ダイアログ
    await waitFor(() => {
      expect(screen.getByText('この経費を承認しますか？')).toBeInTheDocument();
    });

    const confirmButton = screen.getByRole('button', { name: '承認する' });
    await user.click(confirmButton);

    expect(mockApprove).toHaveBeenCalledWith(
      mockPendingApprovals[0].id,
      { comment: '' }
    );
  });

  it('差戻しが機能する', async () => {
    vi.spyOn(expenseApi, 'getPendingApprovals').mockResolvedValue({
      data: mockPendingApprovals,
      total: mockPendingApprovals.length,
    });

    const mockReject = vi.spyOn(expenseApi, 'rejectExpense').mockResolvedValue({
      success: true,
    });

    render(<ExpenseApprovalList />, { wrapper: createWrapper() });

    await waitFor(() => {
      const rejectButtons = screen.getAllByRole('button', { name: '差戻' });
      expect(rejectButtons.length).toBeGreaterThan(0);
    });

    const firstRejectButton = screen.getAllByRole('button', { name: '差戻' })[0];
    await user.click(firstRejectButton);

    // 差戻し理由入力ダイアログ
    await waitFor(() => {
      expect(screen.getByText('差戻し理由を入力してください')).toBeInTheDocument();
    });

    const reasonInput = screen.getByRole('textbox', { name: '理由' });
    await user.type(reasonInput, '領収書が不鮮明です');

    const submitButton = screen.getByRole('button', { name: '差戻す' });
    await user.click(submitButton);

    expect(mockReject).toHaveBeenCalledWith(
      mockPendingApprovals[0].id,
      { reason: '領収書が不鮮明です' }
    );
  });

  it('一括承認が機能する', async () => {
    vi.spyOn(expenseApi, 'getPendingApprovals').mockResolvedValue({
      data: mockPendingApprovals,
      total: mockPendingApprovals.length,
    });

    const mockBulkApprove = vi.spyOn(expenseApi, 'bulkApproveExpenses').mockResolvedValue({
      success: true,
      approvedCount: 3,
    });

    render(<ExpenseApprovalList />, { wrapper: createWrapper() });

    await waitFor(() => {
      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes.length).toBeGreaterThan(1); // ヘッダーのチェックボックス + 各行
    });

    // 複数選択
    const checkboxes = screen.getAllByRole('checkbox');
    await user.click(checkboxes[1]); // 1つ目の経費
    await user.click(checkboxes[2]); // 2つ目の経費

    // 一括承認ボタンが表示される
    const bulkApproveButton = screen.getByRole('button', { name: '一括承認' });
    expect(bulkApproveButton).toBeInTheDocument();

    await user.click(bulkApproveButton);

    // 確認ダイアログ
    await waitFor(() => {
      expect(screen.getByText('2件の経費を承認しますか？')).toBeInTheDocument();
    });

    const confirmButton = screen.getByRole('button', { name: '承認する' });
    await user.click(confirmButton);

    expect(mockBulkApprove).toHaveBeenCalledWith(
      expect.arrayContaining([
        mockPendingApprovals[0].id,
        mockPendingApprovals[1].id,
      ])
    );
  });
});

describe('ReceiptUpload', () => {
  const user = userEvent.setup();
  const mockOnUpload = vi.fn();
  const mockOnRemove = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('領収書アップロードコンポーネントが正しくレンダリングされる', () => {
    render(
      <ReceiptUpload onUpload={mockOnUpload} onRemove={mockOnRemove} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('領収書を撮影またはアップロード')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'カメラ' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'ファイル' })).toBeInTheDocument();
  });

  it('ファイルアップロードが機能する', async () => {
    const mockFile = new File(['receipt content'], 'receipt.pdf', { type: 'application/pdf' });

    render(
      <ReceiptUpload onUpload={mockOnUpload} onRemove={mockOnRemove} />,
      { wrapper: createWrapper() }
    );

    const fileButton = screen.getByRole('button', { name: 'ファイル' });
    await user.click(fileButton);

    const fileInput = screen.getByTestId('file-input');
    await user.upload(fileInput, mockFile);

    await waitFor(() => {
      expect(mockOnUpload).toHaveBeenCalledWith(mockFile);
    });
  });

  it('カメラ撮影が機能する（モバイル環境）', async () => {
    // モバイル環境をシミュレート
    Object.defineProperty(navigator, 'mediaDevices', {
      value: {
        getUserMedia: vi.fn().mockResolvedValue({
          getTracks: () => [],
        }),
      },
      writable: true,
    });

    render(
      <ReceiptUpload onUpload={mockOnUpload} onRemove={mockOnRemove} />,
      { wrapper: createWrapper() }
    );

    const cameraButton = screen.getByRole('button', { name: 'カメラ' });
    await user.click(cameraButton);

    await waitFor(() => {
      expect(screen.getByTestId('camera-preview')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '撮影' })).toBeInTheDocument();
    });
  });

  it('アップロード済みファイルの削除が機能する', async () => {
    const uploadedFile = {
      id: '1',
      name: 'receipt.jpg',
      url: '/uploads/receipt.jpg',
    };

    render(
      <ReceiptUpload 
        onUpload={mockOnUpload} 
        onRemove={mockOnRemove}
        uploadedFiles={[uploadedFile]}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('receipt.jpg')).toBeInTheDocument();

    const removeButton = screen.getByRole('button', { name: '削除' });
    await user.click(removeButton);

    expect(mockOnRemove).toHaveBeenCalledWith(uploadedFile.id);
  });
});

describe('ExpenseOCR', () => {
  const user = userEvent.setup();
  const mockOnComplete = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('OCR処理画面が正しく表示される', () => {
    render(
      <ExpenseOCR 
        imageUrl="/uploads/receipt.jpg"
        onComplete={mockOnComplete}
        onCancel={mockOnCancel}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('領収書をスキャン中...')).toBeInTheDocument();
    expect(screen.getByRole('img', { name: '領収書' })).toHaveAttribute('src', '/uploads/receipt.jpg');
  });

  it('OCR結果の編集が機能する', async () => {
    const mockOcrResult = {
      date: '2024-07-15',
      vendor: 'コンビニA',
      amount: 1500,
      items: [
        { description: '弁当', amount: 500 },
        { description: '飲み物', amount: 200 },
        { description: '文房具', amount: 800 },
      ],
    };

    vi.spyOn(expenseApi, 'processOCR').mockResolvedValue(mockOcrResult);

    render(
      <ExpenseOCR 
        imageUrl="/uploads/receipt.jpg"
        onComplete={mockOnComplete}
        onCancel={mockOnCancel}
      />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue('2024-07-15')).toBeInTheDocument();
      expect(screen.getByDisplayValue('コンビニA')).toBeInTheDocument();
      expect(screen.getByDisplayValue('1500')).toBeInTheDocument();
    });

    // 金額を編集
    const amountInput = screen.getByLabelText('合計金額');
    await user.clear(amountInput);
    await user.type(amountInput, '1600');

    // 確定
    const confirmButton = screen.getByRole('button', { name: '確定' });
    await user.click(confirmButton);

    expect(mockOnComplete).toHaveBeenCalledWith(
      expect.objectContaining({
        ...mockOcrResult,
        amount: 1600,
      })
    );
  });

  it('OCRエラー時の再試行が機能する', async () => {
    const mockProcessOCR = vi.spyOn(expenseApi, 'processOCR')
      .mockRejectedValueOnce(new Error('OCR処理に失敗しました'))
      .mockResolvedValueOnce({
        date: '2024-07-15',
        vendor: 'コンビニA',
        amount: 1500,
        items: [],
      });

    render(
      <ExpenseOCR 
        imageUrl="/uploads/receipt.jpg"
        onComplete={mockOnComplete}
        onCancel={mockOnCancel}
      />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText('OCR処理に失敗しました')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '再試行' })).toBeInTheDocument();
    });

    const retryButton = screen.getByRole('button', { name: '再試行' });
    await user.click(retryButton);

    await waitFor(() => {
      expect(mockProcessOCR).toHaveBeenCalledTimes(2);
      expect(screen.getByDisplayValue('2024-07-15')).toBeInTheDocument();
    });
  });
});