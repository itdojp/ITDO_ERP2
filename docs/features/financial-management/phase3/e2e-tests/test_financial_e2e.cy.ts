/**
 * 財務管理システムE2Eテスト
 * Cypress を使用したエンドツーエンドテスト
 */

describe('財務管理システムE2Eテスト', () => {
  beforeEach(() => {
    // テスト環境のセットアップ
    cy.task('db:seed');
    cy.task('resetEmails');
    
    // ログイン
    cy.login('manager01', 'password123');
    cy.visit('/financial');
  });

  describe('予算管理フロー', () => {
    it('年度予算の作成から承認までの完全なフロー', () => {
      // 1. 予算一覧画面へ移動
      cy.get('[data-testid="nav-budget"]').click();
      cy.url().should('include', '/financial/budgets');

      // 2. 新規予算作成
      cy.get('[data-testid="create-budget-button"]').click();
      cy.url().should('include', '/financial/budgets/new');

      // 予算情報入力
      cy.get('input[name="budgetCode"]').type('BUD-2024-E2E-001');
      cy.get('input[name="budgetName"]').type('2024年度E2Eテスト部門予算');
      cy.get('select[name="fiscalYear"]').select('2024');
      cy.get('input[name="periodStart"]').type('2024-04-01');
      cy.get('input[name="periodEnd"]').type('2025-03-31');
      cy.get('select[name="department"]').select('営業部');
      cy.get('input[name="expenseBudget"]').type('30000000');

      // 保存
      cy.get('button[type="submit"]').contains('作成').click();

      // 3. 作成確認
      cy.url().should('match', /\/financial\/budgets\/\d+$/);
      cy.contains('2024年度E2Eテスト部門予算').should('be.visible');
      cy.contains('¥30,000,000').should('be.visible');
      cy.contains('下書き').should('be.visible');

      // 4. 費目配分
      cy.get('[data-testid="tab-allocation"]').click();
      cy.get('[data-testid="add-allocation-button"]').click();

      // 配分設定
      cy.get('[data-testid="allocation-row-0"] select[name="accountCode"]').select('7001');
      cy.get('[data-testid="allocation-row-0"] input[name="amount"]').type('15000000');
      
      cy.get('[data-testid="add-allocation-row"]').click();
      cy.get('[data-testid="allocation-row-1"] select[name="accountCode"]').select('7002');
      cy.get('[data-testid="allocation-row-1"] input[name="amount"]').type('10000000');

      cy.get('[data-testid="add-allocation-row"]').click();
      cy.get('[data-testid="allocation-row-2"] select[name="accountCode"]').select('7003');
      cy.get('[data-testid="allocation-row-2"] input[name="amount"]').type('5000000');

      cy.get('[data-testid="save-allocation-button"]').click();

      // 配分確認
      cy.contains('配分が保存されました').should('be.visible');

      // 5. 予算承認申請
      cy.get('[data-testid="submit-approval-button"]').click();
      cy.get('[data-testid="confirm-submit-dialog"]').should('be.visible');
      cy.get('[data-testid="confirm-submit-button"]').click();

      // ステータス変更確認
      cy.contains('承認待ち').should('be.visible');

      // 6. 部長でログインして承認
      cy.logout();
      cy.login('director01', 'password123');
      cy.visit('/financial/budgets');

      // 承認待ちフィルタ
      cy.get('select[name="status"]').select('pending');
      cy.contains('2024年度E2Eテスト部門予算').click();

      // 承認実行
      cy.get('[data-testid="approve-button"]').click();
      cy.get('textarea[name="comment"]').type('問題ありません。承認します。');
      cy.get('[data-testid="confirm-approve-button"]').click();

      // 承認確認
      cy.contains('承認済み').should('be.visible');
      cy.contains('予算が承認されました').should('be.visible');
    });

    it('予算消化状況のモニタリングとアラート', () => {
      // 承認済み予算を選択
      cy.get('[data-testid="nav-budget"]').click();
      cy.get('select[name="status"]').select('approved');
      cy.contains('2024年度営業部予算').click();

      // 消化状況タブ
      cy.get('[data-testid="tab-consumption"]').click();

      // グラフ表示確認
      cy.get('[data-testid="consumption-chart"]').should('be.visible');
      cy.get('[data-testid="consumption-rate"]').should('contain', '%');

      // 費目別消化状況
      cy.get('[data-testid="consumption-table"]').within(() => {
        cy.get('tr').should('have.length.greaterThan', 1);
        cy.contains('交通費').should('be.visible');
        cy.contains('会議費').should('be.visible');
        cy.contains('交際費').should('be.visible');
      });

      // アラート確認（80%超過の費目がある場合）
      cy.get('[data-testid="budget-alerts"]').within(() => {
        cy.get('.alert-warning').should('exist');
        cy.contains('80%').should('be.visible');
      });
    });
  });

  describe('経費申請・承認フロー', () => {
    it('経費申請から精算までの完全なフロー', () => {
      // 1. 経費申請画面へ
      cy.get('[data-testid="nav-expense"]').click();
      cy.get('[data-testid="create-expense-button"]').click();

      // 2. 経費情報入力
      cy.get('input[name="expenseDate"]').type('2024-07-15');
      cy.get('select[name="department"]').select('営業部');
      cy.get('select[name="project"]').select('PRJ-001');

      // 明細1
      cy.get('[data-testid="expense-item-0"] select[name="type"]').select('transport');
      cy.get('[data-testid="expense-item-0"] input[name="description"]').type('東京→大阪 新幹線代');
      cy.get('[data-testid="expense-item-0"] input[name="amount"]').type('28500');
      cy.get('[data-testid="expense-item-0"] select[name="taxRate"]').select('10');

      // 明細追加
      cy.get('[data-testid="add-item-button"]').click();
      cy.get('[data-testid="expense-item-1"] select[name="type"]').select('meeting');
      cy.get('[data-testid="expense-item-1"] input[name="description"]').type('顧客との会食');
      cy.get('[data-testid="expense-item-1"] input[name="amount"]').type('15000');
      cy.get('[data-testid="expense-item-1"] input[name="vendor"]').type('レストラン山田');
      cy.get('[data-testid="expense-item-1"] input[name="attendees"]').type('顧客A社 山田様、田中様');

      // 3. 領収書アップロード
      cy.get('[data-testid="receipt-upload-0"]').attachFile('receipt1.jpg');
      cy.get('[data-testid="receipt-upload-1"]').attachFile('receipt2.jpg');

      // アップロード確認
      cy.get('[data-testid="receipt-preview-0"]').should('be.visible');
      cy.get('[data-testid="receipt-preview-1"]').should('be.visible');

      // 4. 申請
      cy.get('button[type="submit"]').contains('申請').click();

      // 申請確認
      cy.contains('経費申請が完了しました').should('be.visible');
      cy.url().should('match', /\/financial\/expenses\/\d+$/);

      // 申請番号を取得
      cy.get('[data-testid="expense-number"]').invoke('text').as('expenseNumber');

      // 5. マネージャーで承認
      cy.logout();
      cy.login('manager01', 'password123');
      cy.visit('/financial/expenses/approvals');

      // 承認待ち一覧
      cy.get('@expenseNumber').then((expenseNumber) => {
        cy.contains(expenseNumber).should('be.visible');
        cy.contains(expenseNumber).parents('tr').within(() => {
          cy.get('[data-testid="approve-button"]').click();
        });
      });

      // 承認確認ダイアログ
      cy.get('[data-testid="approval-dialog"]').should('be.visible');
      cy.get('textarea[name="comment"]').type('問題ありません');
      cy.get('[data-testid="confirm-approve-button"]').click();

      // 承認完了確認
      cy.contains('経費が承認されました').should('be.visible');

      // 6. 月次精算確認
      cy.visit('/financial/expenses/settlements');
      cy.get('[data-testid="create-settlement-button"]').should('be.visible');
    });

    it('OCR機能を使用した経費申請', () => {
      cy.get('[data-testid="nav-expense"]').click();
      cy.get('[data-testid="create-expense-button"]').click();

      // OCRボタンをクリック
      cy.get('[data-testid="ocr-button"]').click();

      // 領収書画像をアップロード
      cy.get('input[type="file"]').attachFile('receipt_for_ocr.jpg');

      // OCR処理待機
      cy.get('[data-testid="ocr-processing"]').should('be.visible');
      cy.wait(3000); // OCR処理を待つ

      // OCR結果確認
      cy.get('[data-testid="ocr-result"]').should('be.visible');
      cy.get('input[name="ocrDate"]').should('have.value', '2024-07-15');
      cy.get('input[name="ocrVendor"]').should('have.value', 'コンビニA');
      cy.get('input[name="ocrAmount"]').should('have.value', '1500');

      // OCR結果を確定
      cy.get('[data-testid="confirm-ocr-button"]').click();

      // フォームに反映されたことを確認
      cy.get('input[name="expenseDate"]').should('have.value', '2024-07-15');
      cy.get('[data-testid="expense-item-0"] input[name="amount"]').should('have.value', '1500');
    });
  });

  describe('請求・入金管理フロー', () => {
    it('見積書から請求書作成、送付、入金消込までのフロー', () => {
      // 1. 見積書作成
      cy.get('[data-testid="nav-invoice"]').click();
      cy.get('[data-testid="nav-quotes"]').click();
      cy.get('[data-testid="create-quote-button"]').click();

      // 見積情報入力
      cy.get('select[name="customer"]').select('ABC商事');
      cy.get('input[name="quoteDate"]').type('2024-07-15');
      cy.get('input[name="validUntil"]').type('2024-08-31');
      cy.get('input[name="subject"]').type('システム開発見積');

      // 明細入力
      cy.get('input[name="items[0].description"]').type('要件定義・設計');
      cy.get('input[name="items[0].quantity"]').type('2');
      cy.get('input[name="items[0].unitPrice"]').type('500000');

      cy.get('[data-testid="add-line-button"]').click();
      cy.get('input[name="items[1].description"]').type('開発・実装');
      cy.get('input[name="items[1].quantity"]').type('3');
      cy.get('input[name="items[1].unitPrice"]').type('800000');

      // 割引追加
      cy.get('[data-testid="add-discount-button"]').click();
      cy.get('select[name="discountType"]').select('percentage');
      cy.get('input[name="discountValue"]').type('5');

      // 保存
      cy.get('button[type="submit"]').contains('作成').click();

      // 見積番号を取得
      cy.get('[data-testid="quote-number"]').invoke('text').as('quoteNumber');

      // 2. 見積書から請求書に変換
      cy.get('[data-testid="convert-to-invoice-button"]').click();
      cy.get('[data-testid="confirm-convert-dialog"]').should('be.visible');
      cy.get('input[name="invoiceDate"]').type('2024-07-31');
      cy.get('input[name="dueDate"]').type('2024-08-31');
      cy.get('[data-testid="confirm-convert-button"]').click();

      // 請求書画面に遷移
      cy.url().should('include', '/financial/invoices/');
      cy.contains('請求書が作成されました').should('be.visible');

      // 3. 請求書確認と送付
      cy.get('[data-testid="invoice-number"]').invoke('text').as('invoiceNumber');
      cy.get('[data-testid="send-invoice-button"]').click();

      // 送付先設定
      cy.get('input[name="recipients"]').type('accounting@abc-corp.jp');
      cy.get('input[name="cc"]').type('manager@abc-corp.jp');
      cy.get('textarea[name="message"]').type('7月分のご請求書をお送りします。\nよろしくお願いいたします。');

      // 送信
      cy.get('[data-testid="confirm-send-button"]').click();
      cy.contains('請求書が送信されました').should('be.visible');

      // メール送信確認
      cy.task('getLastEmail').then((email: any) => {
        expect(email.to).to.include('accounting@abc-corp.jp');
        expect(email.subject).to.include('請求書');
        expect(email.attachments).to.have.length(1);
      });

      // 4. 入金登録と消込
      cy.visit('/financial/payments/reconciliation');

      // 銀行データインポート（シミュレート）
      cy.get('[data-testid="import-bank-data"]').click();
      cy.get('input[type="file"]').attachFile('bank_data.csv');
      cy.get('[data-testid="confirm-import-button"]').click();

      // インポート結果確認
      cy.contains('3件の入金データを取り込みました').should('be.visible');

      // 自動マッチング実行
      cy.get('[data-testid="auto-match-button"]').click();
      cy.wait(2000);

      // マッチング結果確認
      cy.get('@invoiceNumber').then((invoiceNumber) => {
        cy.get('[data-testid="matched-pairs"]').within(() => {
          cy.contains(invoiceNumber).should('be.visible');
          cy.contains('自動マッチ').should('be.visible');
        });
      });

      // 消込実行
      cy.get('[data-testid="execute-reconciliation-button"]').click();
      cy.get('[data-testid="confirm-reconciliation-dialog"]').should('be.visible');
      cy.get('[data-testid="confirm-button"]').click();

      // 消込完了確認
      cy.contains('消込が完了しました').should('be.visible');

      // 請求書のステータス確認
      cy.get('@invoiceNumber').then((invoiceNumber) => {
        cy.visit('/financial/invoices');
        cy.contains(invoiceNumber).parents('tr').within(() => {
          cy.contains('支払済み').should('be.visible');
        });
      });
    });

    it('定期請求の設定と自動生成', () => {
      // 定期請求設定画面へ
      cy.get('[data-testid="nav-invoice"]').click();
      cy.get('[data-testid="nav-recurring"]').click();
      cy.get('[data-testid="create-recurring-button"]').click();

      // 設定入力
      cy.get('select[name="customer"]').select('定期顧客株式会社');
      cy.get('select[name="frequency"]').select('monthly');
      cy.get('input[name="startDate"]').type('2024-08-01');
      cy.get('input[name="endDate"]').type('2025-07-31');
      cy.get('input[name="dayOfMonth"]').type('25');

      // テンプレート明細
      cy.get('input[name="template.description"]').type('月額サービス利用料');
      cy.get('input[name="template.unitPrice"]').type('100000');

      // 保存
      cy.get('button[type="submit"]').contains('設定').click();

      // 設定確認
      cy.contains('定期請求が設定されました').should('be.visible');

      // バッチ実行シミュレート
      cy.task('runRecurringInvoiceBatch', { date: '2024-08-25' });

      // 生成された請求書確認
      cy.visit('/financial/invoices');
      cy.get('input[name="dateFilter"]').type('2024-08-25');
      cy.contains('定期顧客株式会社').should('be.visible');
      cy.contains('月額サービス利用料').should('be.visible');
    });
  });

  describe('財務レポート・分析', () => {
    it('月次試算表の表示とエクスポート', () => {
      cy.get('[data-testid="nav-reports"]').click();
      cy.get('[data-testid="nav-trial-balance"]').click();

      // 期間選択
      cy.get('select[name="year"]').select('2024');
      cy.get('select[name="month"]').select('7');
      cy.get('[data-testid="load-report-button"]').click();

      // レポート表示待機
      cy.get('[data-testid="trial-balance-table"]').should('be.visible');

      // 借方・貸方の一致確認
      cy.get('[data-testid="total-debit"]').invoke('text').then((debit) => {
        cy.get('[data-testid="total-credit"]').invoke('text').should('equal', debit);
      });

      // エクスポート
      cy.get('[data-testid="export-button"]').click();
      cy.get('[data-testid="export-format-excel"]').click();
      cy.get('[data-testid="confirm-export-button"]').click();

      // ダウンロード確認
      cy.readFile('cypress/downloads/試算表_2024年7月.xlsx').should('exist');
    });

    it('予実対比分析の実行', () => {
      cy.get('[data-testid="nav-reports"]').click();
      cy.get('[data-testid="nav-budget-actual"]').click();

      // 分析条件設定
      cy.get('select[name="fiscalYear"]').select('2024');
      cy.get('select[name="period"]').select('Q2');
      cy.get('select[name="department"]').select('全社');
      cy.get('[data-testid="analyze-button"]').click();

      // 分析結果表示
      cy.get('[data-testid="analysis-result"]').should('be.visible');

      // 主要指標確認
      cy.get('[data-testid="revenue-achievement"]').should('contain', '%');
      cy.get('[data-testid="cost-variance"]').should('be.visible');
      cy.get('[data-testid="profit-rate"]').should('be.visible');

      // グラフ表示
      cy.get('[data-testid="variance-chart"]').should('be.visible');
      cy.get('[data-testid="trend-chart"]').should('be.visible');

      // ドリルダウン
      cy.get('[data-testid="expense-row"]').first().click();
      cy.get('[data-testid="expense-detail-modal"]').should('be.visible');
      cy.get('[data-testid="account-breakdown"]').should('be.visible');
    });

    it('ダッシュボードのカスタマイズと自動更新', () => {
      cy.visit('/financial/dashboard');

      // ウィジェット追加
      cy.get('[data-testid="customize-dashboard-button"]').click();
      cy.get('[data-testid="widget-catalog"]').should('be.visible');

      // キャッシュフローウィジェット追加
      cy.get('[data-testid="add-cashflow-widget"]').click();
      cy.get('[data-testid="widget-cashflow"]').should('be.visible');

      // 売掛金エージングウィジェット追加
      cy.get('[data-testid="add-aging-widget"]').click();
      cy.get('[data-testid="widget-aging"]').should('be.visible');

      // レイアウト保存
      cy.get('[data-testid="save-layout-button"]').click();

      // 自動更新確認（10秒後）
      cy.get('[data-testid="last-updated"]').invoke('text').then((initialTime) => {
        cy.wait(10000);
        cy.get('[data-testid="last-updated"]').invoke('text').should('not.equal', initialTime);
      });

      // アラート通知確認
      cy.get('[data-testid="alert-panel"]').within(() => {
        cy.get('.alert-item').should('have.length.greaterThan', 0);
      });
    });
  });

  describe('エラーハンドリングとリカバリー', () => {
    it('ネットワークエラー時の適切な処理', () => {
      // ネットワークエラーをシミュレート
      cy.intercept('POST', '/api/v1/expenses', { forceNetworkError: true }).as('createExpense');

      cy.get('[data-testid="nav-expense"]').click();
      cy.get('[data-testid="create-expense-button"]').click();

      // 最小限の入力
      cy.get('select[name="type"]').select('transport');
      cy.get('input[name="amount"]').type('1000');
      cy.get('input[name="description"]').type('テスト');

      // 送信
      cy.get('button[type="submit"]').click();
      cy.wait('@createExpense');

      // エラーメッセージ確認
      cy.contains('ネットワークエラーが発生しました').should('be.visible');
      cy.contains('再試行').should('be.visible');

      // データが保持されていることを確認
      cy.get('input[name="amount"]').should('have.value', '1000');
      cy.get('input[name="description"]').should('have.value', 'テスト');

      // 再試行
      cy.intercept('POST', '/api/v1/expenses', { statusCode: 200, body: { id: 1 } }).as('retryExpense');
      cy.get('[data-testid="retry-button"]').click();
      cy.wait('@retryExpense');

      // 成功確認
      cy.contains('経費申請が完了しました').should('be.visible');
    });

    it('セッションタイムアウト時の処理', () => {
      // 長時間操作をシミュレート
      cy.wait(31 * 60 * 1000); // 31分待機

      // 操作を試行
      cy.get('[data-testid="nav-budget"]').click();

      // セッションタイムアウトダイアログ
      cy.get('[data-testid="session-timeout-dialog"]').should('be.visible');
      cy.contains('セッションがタイムアウトしました').should('be.visible');

      // 再ログイン
      cy.get('[data-testid="relogin-button"]').click();
      cy.get('input[name="username"]').type('manager01');
      cy.get('input[name="password"]').type('password123');
      cy.get('button[type="submit"]').click();

      // 元の画面に戻ることを確認
      cy.url().should('include', '/financial/budgets');
    });
  });
});

// カスタムコマンド定義
Cypress.Commands.add('login', (username: string, password: string) => {
  cy.visit('/login');
  cy.get('input[name="username"]').type(username);
  cy.get('input[name="password"]').type(password);
  cy.get('button[type="submit"]').click();
  cy.url().should('not.include', '/login');
});

Cypress.Commands.add('logout', () => {
  cy.get('[data-testid="user-menu"]').click();
  cy.get('[data-testid="logout-button"]').click();
  cy.url().should('include', '/login');
});

// TypeScript型定義
declare global {
  namespace Cypress {
    interface Chainable {
      login(username: string, password: string): Chainable<void>;
      logout(): Chainable<void>;
    }
  }
}