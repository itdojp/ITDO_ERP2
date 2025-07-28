/**
 * MFA認証フォームコンポーネントのテスト
 * Phase 3: Validation - 失敗するテストを先に作成
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { MFAForm } from '../MFAForm';

describe('MFAForm', () => {
  const mockOnSubmit = vi.fn();
  const mockOnBackupCode = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('レンダリング', () => {
    it('6つの入力フィールドが表示される', () => {
      render(
        <MFAForm
          onSubmit={mockOnSubmit}
          onBackupCode={mockOnBackupCode}
          isLoading={false}
        />
      );

      const inputs = screen.getAllByRole('textbox', { name: /digit/i });
      expect(inputs).toHaveLength(6);
      
      inputs.forEach((input, index) => {
        expect(input).toHaveAttribute('maxLength', '1');
        expect(input).toHaveAttribute('inputMode', 'numeric');
        expect(input).toHaveAttribute('pattern', '[0-9]');
        expect(input).toHaveAttribute('aria-label', `Digit ${index + 1}`);
      });
    });

    it('確認ボタンとバックアップコードリンクが表示される', () => {
      render(
        <MFAForm
          onSubmit={mockOnSubmit}
          onBackupCode={mockOnBackupCode}
          isLoading={false}
        />
      );

      expect(screen.getByRole('button', { name: '確認' })).toBeInTheDocument();
      expect(screen.getByText('バックアップコードを使用')).toBeInTheDocument();
    });

    it('ローディング中は入力とボタンが無効化される', () => {
      render(
        <MFAForm
          onSubmit={mockOnSubmit}
          onBackupCode={mockOnBackupCode}
          isLoading={true}
        />
      );

      const inputs = screen.getAllByRole('textbox', { name: /digit/i });
      inputs.forEach(input => {
        expect(input).toBeDisabled();
      });

      expect(screen.getByRole('button', { name: '確認' })).toBeDisabled();
    });
  });

  describe('入力動作', () => {
    it('数字入力時に次のフィールドに自動フォーカスが移動する', async () => {
      const user = userEvent.setup();
      render(
        <MFAForm
          onSubmit={mockOnSubmit}
          onBackupCode={mockOnBackupCode}
          isLoading={false}
        />
      );

      const inputs = screen.getAllByRole('textbox', { name: /digit/i });
      
      await user.type(inputs[0], '1');
      expect(inputs[1]).toHaveFocus();

      await user.type(inputs[1], '2');
      expect(inputs[2]).toHaveFocus();
    });

    it('バックスペースで前のフィールドに戻る', async () => {
      const user = userEvent.setup();
      render(
        <MFAForm
          onSubmit={mockOnSubmit}
          onBackupCode={mockOnBackupCode}
          isLoading={false}
        />
      );

      const inputs = screen.getAllByRole('textbox', { name: /digit/i });
      
      // 2番目のフィールドにフォーカス
      inputs[1].focus();
      
      await user.keyboard('{Backspace}');
      expect(inputs[0]).toHaveFocus();
    });

    it('数字以外の入力は受け付けない', async () => {
      const user = userEvent.setup();
      render(
        <MFAForm
          onSubmit={mockOnSubmit}
          onBackupCode={mockOnBackupCode}
          isLoading={false}
        />
      );

      const firstInput = screen.getAllByRole('textbox', { name: /digit/i })[0];
      
      await user.type(firstInput, 'a');
      expect(firstInput).toHaveValue('');

      await user.type(firstInput, '!');
      expect(firstInput).toHaveValue('');

      await user.type(firstInput, '5');
      expect(firstInput).toHaveValue('5');
    });

    it('既に値がある場合は上書きされる', async () => {
      const user = userEvent.setup();
      render(
        <MFAForm
          onSubmit={mockOnSubmit}
          onBackupCode={mockOnBackupCode}
          isLoading={false}
        />
      );

      const firstInput = screen.getAllByRole('textbox', { name: /digit/i })[0];
      
      await user.type(firstInput, '1');
      expect(firstInput).toHaveValue('1');

      firstInput.focus();
      await user.type(firstInput, '2');
      expect(firstInput).toHaveValue('2');
    });
  });

  describe('ペースト機能', () => {
    it('6桁の数字をペーストすると全フィールドに入力される', async () => {
      const user = userEvent.setup();
      render(
        <MFAForm
          onSubmit={mockOnSubmit}
          onBackupCode={mockOnBackupCode}
          isLoading={false}
        />
      );

      const inputs = screen.getAllByRole('textbox', { name: /digit/i });
      
      // ペーストイベントをシミュレート
      const pasteEvent = new ClipboardEvent('paste', {
        clipboardData: new DataTransfer(),
      });
      pasteEvent.clipboardData?.setData('text/plain', '123456');
      
      fireEvent.paste(inputs[0], pasteEvent);

      await waitFor(() => {
        expect(inputs[0]).toHaveValue('1');
        expect(inputs[1]).toHaveValue('2');
        expect(inputs[2]).toHaveValue('3');
        expect(inputs[3]).toHaveValue('4');
        expect(inputs[4]).toHaveValue('5');
        expect(inputs[5]).toHaveValue('6');
      });
    });

    it('数字以外を含むペーストは無視される', async () => {
      render(
        <MFAForm
          onSubmit={mockOnSubmit}
          onBackupCode={mockOnBackupCode}
          isLoading={false}
        />
      );

      const inputs = screen.getAllByRole('textbox', { name: /digit/i });
      
      const pasteEvent = new ClipboardEvent('paste', {
        clipboardData: new DataTransfer(),
      });
      pasteEvent.clipboardData?.setData('text/plain', '12a456');
      
      fireEvent.paste(inputs[0], pasteEvent);

      await waitFor(() => {
        inputs.forEach(input => {
          expect(input).toHaveValue('');
        });
      });
    });
  });

  describe('フォーム送信', () => {
    it('6桁すべて入力すると自動的に送信される', async () => {
      const user = userEvent.setup();
      render(
        <MFAForm
          onSubmit={mockOnSubmit}
          onBackupCode={mockOnBackupCode}
          isLoading={false}
        />
      );

      const inputs = screen.getAllByRole('textbox', { name: /digit/i });
      
      for (let i = 0; i < 6; i++) {
        await user.type(inputs[i], String(i + 1));
      }

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith('123456');
      });
    });

    it('確認ボタンクリックで送信される', async () => {
      const user = userEvent.setup();
      render(
        <MFAForm
          onSubmit={mockOnSubmit}
          onBackupCode={mockOnBackupCode}
          isLoading={false}
        />
      );

      const inputs = screen.getAllByRole('textbox', { name: /digit/i });
      
      // 部分的に入力
      await user.type(inputs[0], '1');
      await user.type(inputs[1], '2');
      await user.type(inputs[2], '3');
      await user.type(inputs[3], '4');
      await user.type(inputs[4], '5');
      await user.type(inputs[5], '6');

      const submitButton = screen.getByRole('button', { name: '確認' });
      await user.click(submitButton);

      expect(mockOnSubmit).toHaveBeenCalledWith('123456');
    });

    it('6桁未満では送信されない', async () => {
      const user = userEvent.setup();
      render(
        <MFAForm
          onSubmit={mockOnSubmit}
          onBackupCode={mockOnBackupCode}
          isLoading={false}
        />
      );

      const inputs = screen.getAllByRole('textbox', { name: /digit/i });
      
      // 5桁のみ入力
      for (let i = 0; i < 5; i++) {
        await user.type(inputs[i], String(i + 1));
      }

      const submitButton = screen.getByRole('button', { name: '確認' });
      await user.click(submitButton);

      expect(mockOnSubmit).not.toHaveBeenCalled();
      expect(await screen.findByText('6桁のコードを入力してください')).toBeInTheDocument();
    });
  });

  describe('バックアップコード', () => {
    it('バックアップコードリンククリックで onBackupCode が呼ばれる', async () => {
      const user = userEvent.setup();
      render(
        <MFAForm
          onSubmit={mockOnSubmit}
          onBackupCode={mockOnBackupCode}
          isLoading={false}
        />
      );

      const backupLink = screen.getByText('バックアップコードを使用');
      await user.click(backupLink);

      expect(mockOnBackupCode).toHaveBeenCalled();
    });
  });

  describe('エラー表示', () => {
    it('エラーメッセージが表示される', () => {
      render(
        <MFAForm
          onSubmit={mockOnSubmit}
          onBackupCode={mockOnBackupCode}
          isLoading={false}
          error="認証コードが正しくありません"
        />
      );

      expect(screen.getByRole('alert')).toHaveTextContent('認証コードが正しくありません');
    });

    it('エラー後に再入力でエラーがクリアされる', async () => {
      const user = userEvent.setup();
      const { rerender } = render(
        <MFAForm
          onSubmit={mockOnSubmit}
          onBackupCode={mockOnBackupCode}
          isLoading={false}
          error="認証コードが正しくありません"
        />
      );

      expect(screen.getByRole('alert')).toBeInTheDocument();

      // エラーをクリア
      rerender(
        <MFAForm
          onSubmit={mockOnSubmit}
          onBackupCode={mockOnBackupCode}
          isLoading={false}
        />
      );

      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  describe('キーボードナビゲーション', () => {
    it('矢印キーで前後のフィールドに移動できる', async () => {
      const user = userEvent.setup();
      render(
        <MFAForm
          onSubmit={mockOnSubmit}
          onBackupCode={mockOnBackupCode}
          isLoading={false}
        />
      );

      const inputs = screen.getAllByRole('textbox', { name: /digit/i });
      
      inputs[2].focus();
      
      await user.keyboard('{ArrowLeft}');
      expect(inputs[1]).toHaveFocus();

      await user.keyboard('{ArrowRight}');
      expect(inputs[2]).toHaveFocus();
    });
  });

  describe('タイマー表示', () => {
    it('残り時間インジケーターが表示される', () => {
      render(
        <MFAForm
          onSubmit={mockOnSubmit}
          onBackupCode={mockOnBackupCode}
          isLoading={false}
          showTimer={true}
        />
      );

      expect(screen.getByText(/有効期限/)).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });
});