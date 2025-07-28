/**
 * 請求管理コンポーネントのテスト
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';

// Components
import { InvoiceForm } from '@/components/financial/invoice/InvoiceForm';
import { InvoiceList } from '@/components/financial/invoice/InvoiceList';
import { InvoiceDetail } from '@/components/financial/invoice/InvoiceDetail';
import { InvoicePreview } from '@/components/financial/invoice/InvoicePreview';
import { QuoteForm } from '@/components/financial/invoice/QuoteForm';
import { PaymentReconciliation } from '@/components/financial/invoice/PaymentReconciliation';

// Mocks
import { 
  mockInvoices, 
  mockInvoiceDetail, 
  mockQuotes,
  mockUnallocatedPayments,
  mockUnpaidInvoices 
} from '@/test/mocks/invoice.mock';
import * as invoiceApi from '@/services/api/invoice';
import * as paymentApi from '@/services/api/payment';

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

describe('InvoiceForm', () => {
  const user = userEvent.setup();
  const mockOnSubmit = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('請求書作成フォームが正しくレンダリングされる', () => {
    render(
      <InvoiceForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByLabelText('顧客')).toBeInTheDocument();
    expect(screen.getByLabelText('請求日')).toBeInTheDocument();
    expect(screen.getByLabelText('支払期限')).toBeInTheDocument();
    expect(screen.getByLabelText('件名')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '行追加' })).toBeInTheDocument();
  });

  it('明細行の追加と削除が機能する', async () => {
    render(
      <InvoiceForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />,
      { wrapper: createWrapper() }
    );

    // 初期状態で1行あることを確認
    expect(screen.getAllByTestId('invoice-line-item')).toHaveLength(1);

    // 行を追加
    const addButton = screen.getByRole('button', { name: '行追加' });
    await user.click(addButton);

    expect(screen.getAllByTestId('invoice-line-item')).toHaveLength(2);

    // 行を削除
    const deleteButtons = screen.getAllByRole('button', { name: '削除' });
    await user.click(deleteButtons[0]);

    await waitFor(() => {
      expect(screen.getAllByTestId('invoice-line-item')).toHaveLength(1);
    });
  });

  it('金額計算が正しく行われる', async () => {
    render(
      <InvoiceForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />,
      { wrapper: createWrapper() }
    );

    // 明細を入力
    const descriptionInput = screen.getByPlaceholderText('品目・サービス名');
    const quantityInput = screen.getByLabelText('数量');
    const unitPriceInput = screen.getByLabelText('単価');
    const taxRateSelect = screen.getByLabelText('税率');

    await user.type(descriptionInput, 'コンサルティング料');
    await user.clear(quantityInput);
    await user.type(quantityInput, '2');
    await user.type(unitPriceInput, '500000');
    await user.selectOptions(taxRateSelect, '10');

    await waitFor(() => {
      expect(screen.getByTestId('line-amount-0').textContent).toBe('¥1,000,000');
      expect(screen.getByTestId('subtotal').textContent).toBe('¥1,000,000');
      expect(screen.getByTestId('tax-10').textContent).toBe('¥100,000');
      expect(screen.getByTestId('total').textContent).toBe('¥1,100,000');
    });
  });

  it('適格請求書の設定が機能する', async () => {
    render(
      <InvoiceForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />,
      { wrapper: createWrapper() }
    );

    const qualifiedCheckbox = screen.getByLabelText('適格請求書として発行');
    expect(qualifiedCheckbox).toBeChecked(); // デフォルトでチェック

    await user.click(qualifiedCheckbox);
    expect(qualifiedCheckbox).not.toBeChecked();

    // 登録番号フィールドが非表示になることを確認
    await waitFor(() => {
      expect(screen.queryByLabelText('登録番号')).not.toBeInTheDocument();
    });
  });

  it('見積書から請求書への変換が機能する', async () => {
    const mockQuote = {
      id: 1,
      quoteNumber: 'QT-2024-001',
      customer: { id: 1, name: 'ABC商事' },
      items: [
        {
          description: 'システム開発',
          quantity: 1,
          unitPrice: 1000000,
          taxRate: 10,
        }
      ],
      totalAmount: 1100000,
    };

    render(
      <InvoiceForm 
        onSubmit={mockOnSubmit} 
        onCancel={mockOnCancel}
        quote={mockQuote}
      />,
      { wrapper: createWrapper() }
    );

    // 見積データが反映されていることを確認
    expect(screen.getByDisplayValue('ABC商事')).toBeInTheDocument();
    expect(screen.getByDisplayValue('システム開発')).toBeInTheDocument();
    expect(screen.getByDisplayValue('1000000')).toBeInTheDocument();

    // 変換元の見積番号が表示される
    expect(screen.getByText('見積書 QT-2024-001 から作成')).toBeInTheDocument();
  });
});

describe('InvoiceList', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('請求書一覧が正しく表示される', async () => {
    vi.spyOn(invoiceApi, 'getInvoices').mockResolvedValue({
      data: mockInvoices,
      total: mockInvoices.length,
    });

    render(<InvoiceList />, { wrapper: createWrapper() });

    await waitFor(() => {
      mockInvoices.forEach(invoice => {
        expect(screen.getByText(invoice.invoiceNumber)).toBeInTheDocument();
        expect(screen.getByText(invoice.customer.name)).toBeInTheDocument();
      });
    });

    // ステータスバッジの確認
    expect(screen.getByText('送信済み')).toBeInTheDocument();
    expect(screen.getByText('支払済み')).toBeInTheDocument();
    expect(screen.getByText('期限超過')).toBeInTheDocument();
  });

  it('期間フィルタが機能する', async () => {
    const mockGetInvoices = vi.spyOn(invoiceApi, 'getInvoices').mockResolvedValue({
      data: mockInvoices,
      total: mockInvoices.length,
    });

    render(<InvoiceList />, { wrapper: createWrapper() });

    // 月選択
    const monthSelect = screen.getByLabelText('対象月');
    await user.selectOptions(monthSelect, '2024-07');

    await waitFor(() => {
      expect(mockGetInvoices).toHaveBeenCalledWith(
        expect.objectContaining({
          startDate: '2024-07-01',
          endDate: '2024-07-31',
        })
      );
    });
  });

  it('請求書の一括送信が機能する', async () => {
    vi.spyOn(invoiceApi, 'getInvoices').mockResolvedValue({
      data: mockInvoices.filter(inv => inv.status === 'draft'),
      total: 2,
    });

    const mockBulkSend = vi.spyOn(invoiceApi, 'bulkSendInvoices').mockResolvedValue({
      success: true,
      sentCount: 2,
    });

    render(<InvoiceList />, { wrapper: createWrapper() });

    await waitFor(() => {
      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes.length).toBeGreaterThan(1);
    });

    // 複数選択
    const checkboxes = screen.getAllByRole('checkbox');
    await user.click(checkboxes[1]);
    await user.click(checkboxes[2]);

    // 一括送信ボタン
    const bulkSendButton = screen.getByRole('button', { name: '一括送信' });
    await user.click(bulkSendButton);

    // 確認ダイアログ
    await waitFor(() => {
      expect(screen.getByText('2件の請求書を送信しますか？')).toBeInTheDocument();
    });

    const confirmButton = screen.getByRole('button', { name: '送信する' });
    await user.click(confirmButton);

    expect(mockBulkSend).toHaveBeenCalled();
  });

  it('請求書のエクスポートが機能する', async () => {
    vi.spyOn(invoiceApi, 'getInvoices').mockResolvedValue({
      data: mockInvoices,
      total: mockInvoices.length,
    });

    const mockExport = vi.spyOn(invoiceApi, 'exportInvoices').mockResolvedValue({
      url: '/exports/invoices_202407.xlsx',
    });

    render(<InvoiceList />, { wrapper: createWrapper() });

    const exportButton = await screen.findByRole('button', { name: 'エクスポート' });
    await user.click(exportButton);

    // エクスポート形式選択
    await waitFor(() => {
      expect(screen.getByText('エクスポート形式を選択')).toBeInTheDocument();
    });

    const excelOption = screen.getByLabelText('Excel形式');
    await user.click(excelOption);

    const downloadButton = screen.getByRole('button', { name: 'ダウンロード' });
    await user.click(downloadButton);

    expect(mockExport).toHaveBeenCalledWith({
      format: 'excel',
      period: expect.any(String),
    });
  });
});

describe('InvoiceDetail', () => {
  const invoiceId = 1;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('請求書詳細が正しく表示される', async () => {
    vi.spyOn(invoiceApi, 'getInvoice').mockResolvedValue(mockInvoiceDetail);

    render(<InvoiceDetail invoiceId={invoiceId} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('INV-2024-0731-001')).toBeInTheDocument();
      expect(screen.getByText('ABC商事株式会社')).toBeInTheDocument();
      expect(screen.getByText('¥1,430,000')).toBeInTheDocument();
    });

    // 明細の確認
    expect(screen.getByText('コンサルティング料（7月分）')).toBeInTheDocument();
    expect(screen.getByText('システム保守料（7月分）')).toBeInTheDocument();
  });

  it('請求書のPDFダウンロードが機能する', async () => {
    vi.spyOn(invoiceApi, 'getInvoice').mockResolvedValue(mockInvoiceDetail);
    
    const mockDownloadPDF = vi.spyOn(invoiceApi, 'downloadInvoicePDF').mockResolvedValue({
      url: '/api/invoices/1/pdf',
    });

    render(<InvoiceDetail invoiceId={invoiceId} />, { wrapper: createWrapper() });

    const pdfButton = await screen.findByRole('button', { name: 'PDF出力' });
    await user.click(pdfButton);

    expect(mockDownloadPDF).toHaveBeenCalledWith(invoiceId);
  });

  it('請求書の送信が機能する', async () => {
    const draftInvoice = { ...mockInvoiceDetail, status: 'draft' };
    vi.spyOn(invoiceApi, 'getInvoice').mockResolvedValue(draftInvoice);

    const mockSend = vi.spyOn(invoiceApi, 'sendInvoice').mockResolvedValue({
      success: true,
    });

    render(<InvoiceDetail invoiceId={invoiceId} />, { wrapper: createWrapper() });

    const sendButton = await screen.findByRole('button', { name: '送信' });
    await user.click(sendButton);

    // 送信確認ダイアログ
    await waitFor(() => {
      expect(screen.getByText('請求書送信')).toBeInTheDocument();
    });

    // 宛先入力
    const recipientInput = screen.getByLabelText('宛先');
    await user.type(recipientInput, 'accounting@abc-corp.jp');

    // メッセージ入力
    const messageInput = screen.getByLabelText('メッセージ');
    await user.type(messageInput, '7月分のご請求書をお送りします。');

    const confirmSendButton = screen.getByRole('button', { name: '送信する' });
    await user.click(confirmSendButton);

    expect(mockSend).toHaveBeenCalledWith(invoiceId, {
      recipients: ['accounting@abc-corp.jp'],
      message: '7月分のご請求書をお送りします。',
    });
  });

  it('支払履歴が表示される', async () => {
    const paidInvoice = {
      ...mockInvoiceDetail,
      status: 'paid',
      payments: [
        {
          id: 1,
          paymentDate: '2024-08-30',
          amount: 1430000,
          paymentMethod: 'bank_transfer',
          reference: '振込-20240830-001',
        }
      ],
    };

    vi.spyOn(invoiceApi, 'getInvoice').mockResolvedValue(paidInvoice);

    render(<InvoiceDetail invoiceId={invoiceId} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('支払履歴')).toBeInTheDocument();
      expect(screen.getByText('2024-08-30')).toBeInTheDocument();
      expect(screen.getByText('¥1,430,000')).toBeInTheDocument();
      expect(screen.getByText('銀行振込')).toBeInTheDocument();
    });
  });
});

describe('QuoteForm', () => {
  const user = userEvent.setup();
  const mockOnSubmit = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('見積書作成フォームが正しくレンダリングされる', () => {
    render(
      <QuoteForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByLabelText('顧客')).toBeInTheDocument();
    expect(screen.getByLabelText('見積日')).toBeInTheDocument();
    expect(screen.getByLabelText('有効期限')).toBeInTheDocument();
    expect(screen.getByLabelText('件名')).toBeInTheDocument();
  });

  it('割引設定が機能する', async () => {
    render(
      <QuoteForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />,
      { wrapper: createWrapper() }
    );

    // 明細を入力
    await user.type(screen.getByPlaceholderText('品目・サービス名'), 'コンサルティング');
    await user.type(screen.getByLabelText('単価'), '1000000');

    // 割引を追加
    const addDiscountButton = screen.getByRole('button', { name: '割引を追加' });
    await user.click(addDiscountButton);

    await waitFor(() => {
      expect(screen.getByLabelText('割引タイプ')).toBeInTheDocument();
    });

    // パーセント割引を設定
    const discountTypeSelect = screen.getByLabelText('割引タイプ');
    await user.selectOptions(discountTypeSelect, 'percentage');

    const discountValueInput = screen.getByLabelText('割引率');
    await user.type(discountValueInput, '10');

    await waitFor(() => {
      expect(screen.getByTestId('discount-amount').textContent).toBe('-¥100,000');
      expect(screen.getByTestId('total').textContent).toBe('¥990,000'); // 税込み
    });
  });

  it('見積書の有効期限検証が機能する', async () => {
    render(
      <QuoteForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />,
      { wrapper: createWrapper() }
    );

    // 過去の日付を設定
    const validUntilInput = screen.getByLabelText('有効期限');
    await user.type(validUntilInput, '2023-01-01');

    const submitButton = screen.getByRole('button', { name: '作成' });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('有効期限は見積日以降の日付を指定してください')).toBeInTheDocument();
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });
  });
});

describe('PaymentReconciliation', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('入金消込画面が正しく表示される', async () => {
    vi.spyOn(paymentApi, 'getUnallocatedPayments').mockResolvedValue(mockUnallocatedPayments);
    vi.spyOn(invoiceApi, 'getUnpaidInvoices').mockResolvedValue(mockUnpaidInvoices);

    render(<PaymentReconciliation />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('未消込入金')).toBeInTheDocument();
      expect(screen.getByText('未消込請求書')).toBeInTheDocument();
    });

    // 入金データの表示
    mockUnallocatedPayments.forEach(payment => {
      expect(screen.getByText(`¥${payment.amount.toLocaleString()}`)).toBeInTheDocument();
    });

    // 請求書データの表示
    mockUnpaidInvoices.forEach(invoice => {
      expect(screen.getByText(invoice.invoiceNumber)).toBeInTheDocument();
    });
  });

  it('自動マッチングが機能する', async () => {
    vi.spyOn(paymentApi, 'getUnallocatedPayments').mockResolvedValue(mockUnallocatedPayments);
    vi.spyOn(invoiceApi, 'getUnpaidInvoices').mockResolvedValue(mockUnpaidInvoices);

    const mockAutoMatch = vi.spyOn(paymentApi, 'autoMatchPayments').mockResolvedValue({
      matches: [
        {
          paymentId: 1,
          invoiceId: 1,
          confidence: 0.95,
        }
      ],
    });

    render(<PaymentReconciliation />, { wrapper: createWrapper() });

    const autoMatchButton = await screen.findByRole('button', { name: '自動マッチング' });
    await user.click(autoMatchButton);

    await waitFor(() => {
      expect(mockAutoMatch).toHaveBeenCalled();
      expect(screen.getByText('自動マッチ ✓')).toBeInTheDocument();
    });
  });

  it('手動消込が機能する', async () => {
    vi.spyOn(paymentApi, 'getUnallocatedPayments').mockResolvedValue(mockUnallocatedPayments);
    vi.spyOn(invoiceApi, 'getUnpaidInvoices').mockResolvedValue(mockUnpaidInvoices);

    const mockAllocate = vi.spyOn(paymentApi, 'allocatePayment').mockResolvedValue({
      success: true,
    });

    render(<PaymentReconciliation />, { wrapper: createWrapper() });

    await waitFor(() => {
      const paymentRows = screen.getAllByTestId(/payment-row-/);
      const invoiceRows = screen.getAllByTestId(/invoice-row-/);
      expect(paymentRows.length).toBeGreaterThan(0);
      expect(invoiceRows.length).toBeGreaterThan(0);
    });

    // ドラッグ&ドロップシミュレーション
    const paymentRow = screen.getByTestId('payment-row-1');
    const invoiceRow = screen.getByTestId('invoice-row-1');

    fireEvent.dragStart(paymentRow);
    fireEvent.dragEnter(invoiceRow);
    fireEvent.drop(invoiceRow);

    // 確認ダイアログ
    await waitFor(() => {
      expect(screen.getByText('消込を実行しますか？')).toBeInTheDocument();
    });

    const confirmButton = screen.getByRole('button', { name: '実行' });
    await user.click(confirmButton);

    expect(mockAllocate).toHaveBeenCalledWith({
      paymentId: 1,
      invoiceId: 1,
    });
  });

  it('差額処理オプションが表示される', async () => {
    const paymentsWithDifference = [
      {
        ...mockUnallocatedPayments[0],
        amount: 108000, // 請求額より少ない
      }
    ];

    vi.spyOn(paymentApi, 'getUnallocatedPayments').mockResolvedValue(paymentsWithDifference);
    vi.spyOn(invoiceApi, 'getUnpaidInvoices').mockResolvedValue([
      {
        ...mockUnpaidInvoices[0],
        totalAmount: 110000,
      }
    ]);

    render(<PaymentReconciliation />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('差額: -¥2,000')).toBeInTheDocument();
    });

    // 差額処理オプション
    expect(screen.getByLabelText('値引処理')).toBeInTheDocument();
    expect(screen.getByLabelText('次回請求で調整')).toBeInTheDocument();
  });
});