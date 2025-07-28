/**
 * ログインフォームコンポーネントのテスト
 * Phase 3: Validation - 失敗するテストを先に作成
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { LoginForm } from '../LoginForm';

describe('LoginForm', () => {
  const mockOnSubmit = vi.fn();
  const mockOnGoogleLogin = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('レンダリング', () => {
    it('必要な入力フィールドとボタンが表示される', () => {
      render(
        <LoginForm
          onSubmit={mockOnSubmit}
          onGoogleLogin={mockOnGoogleLogin}
          isLoading={false}
        />
      );

      expect(screen.getByLabelText('メールアドレス')).toBeInTheDocument();
      expect(screen.getByLabelText('パスワード')).toBeInTheDocument();
      expect(screen.getByLabelText('ログイン状態を保持する')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'ログイン' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Googleでログイン' })).toBeInTheDocument();
      expect(screen.getByText('パスワードを忘れた方')).toBeInTheDocument();
    });

    it('ローディング中は入力とボタンが無効化される', () => {
      render(
        <LoginForm
          onSubmit={mockOnSubmit}
          onGoogleLogin={mockOnGoogleLogin}
          isLoading={true}
        />
      );

      expect(screen.getByLabelText('メールアドレス')).toBeDisabled();
      expect(screen.getByLabelText('パスワード')).toBeDisabled();
      expect(screen.getByRole('button', { name: 'ログイン' })).toBeDisabled();
      expect(screen.getByRole('button', { name: 'Googleでログイン' })).toBeDisabled();
    });
  });

  describe('バリデーション', () => {
    it('空のフォームで送信するとエラーが表示される', async () => {
      const user = userEvent.setup();
      render(
        <LoginForm
          onSubmit={mockOnSubmit}
          onGoogleLogin={mockOnGoogleLogin}
          isLoading={false}
        />
      );

      const submitButton = screen.getByRole('button', { name: 'ログイン' });
      await user.click(submitButton);

      expect(await screen.findByText('メールアドレスを入力してください')).toBeInTheDocument();
      expect(await screen.findByText('パスワードを入力してください')).toBeInTheDocument();
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('無効なメールアドレス形式でエラーが表示される', async () => {
      const user = userEvent.setup();
      render(
        <LoginForm
          onSubmit={mockOnSubmit}
          onGoogleLogin={mockOnGoogleLogin}
          isLoading={false}
        />
      );

      const emailInput = screen.getByLabelText('メールアドレス');
      await user.type(emailInput, 'invalid-email');
      await user.tab(); // フォーカスを外す

      expect(await screen.findByText('メールアドレスの形式が正しくありません')).toBeInTheDocument();
    });

    it('パスワードが8文字未満でエラーが表示される', async () => {
      const user = userEvent.setup();
      render(
        <LoginForm
          onSubmit={mockOnSubmit}
          onGoogleLogin={mockOnGoogleLogin}
          isLoading={false}
        />
      );

      const passwordInput = screen.getByLabelText('パスワード');
      await user.type(passwordInput, 'short');
      await user.tab();

      expect(await screen.findByText('パスワードは8文字以上で入力してください')).toBeInTheDocument();
    });
  });

  describe('フォーム送信', () => {
    it('有効な入力で送信すると onSubmit が呼ばれる', async () => {
      const user = userEvent.setup();
      render(
        <LoginForm
          onSubmit={mockOnSubmit}
          onGoogleLogin={mockOnGoogleLogin}
          isLoading={false}
        />
      );

      const emailInput = screen.getByLabelText('メールアドレス');
      const passwordInput = screen.getByLabelText('パスワード');
      const rememberMeCheckbox = screen.getByLabelText('ログイン状態を保持する');

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'SecurePass123!');
      await user.click(rememberMeCheckbox);

      const submitButton = screen.getByRole('button', { name: 'ログイン' });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          'test@example.com',
          'SecurePass123!',
          true
        );
      });
    });

    it('Enterキーでフォームが送信される', async () => {
      const user = userEvent.setup();
      render(
        <LoginForm
          onSubmit={mockOnSubmit}
          onGoogleLogin={mockOnGoogleLogin}
          isLoading={false}
        />
      );

      const emailInput = screen.getByLabelText('メールアドレス');
      const passwordInput = screen.getByLabelText('パスワード');

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'SecurePass123!');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalled();
      });
    });
  });

  describe('Googleログイン', () => {
    it('Googleログインボタンクリックで onGoogleLogin が呼ばれる', async () => {
      const user = userEvent.setup();
      render(
        <LoginForm
          onSubmit={mockOnSubmit}
          onGoogleLogin={mockOnGoogleLogin}
          isLoading={false}
        />
      );

      const googleButton = screen.getByRole('button', { name: 'Googleでログイン' });
      await user.click(googleButton);

      expect(mockOnGoogleLogin).toHaveBeenCalled();
    });
  });

  describe('エラー表示', () => {
    it('認証エラーメッセージが表示される', () => {
      render(
        <LoginForm
          onSubmit={mockOnSubmit}
          onGoogleLogin={mockOnGoogleLogin}
          isLoading={false}
          error="メールアドレスまたはパスワードが正しくありません"
        />
      );

      expect(screen.getByRole('alert')).toHaveTextContent(
        'メールアドレスまたはパスワードが正しくありません'
      );
    });
  });

  describe('アクセシビリティ', () => {
    it('フォームフィールドに適切な aria 属性がある', () => {
      render(
        <LoginForm
          onSubmit={mockOnSubmit}
          onGoogleLogin={mockOnGoogleLogin}
          isLoading={false}
        />
      );

      const emailInput = screen.getByLabelText('メールアドレス');
      expect(emailInput).toHaveAttribute('type', 'email');
      expect(emailInput).toHaveAttribute('autocomplete', 'email');
      expect(emailInput).toHaveAttribute('required');

      const passwordInput = screen.getByLabelText('パスワード');
      expect(passwordInput).toHaveAttribute('type', 'password');
      expect(passwordInput).toHaveAttribute('autocomplete', 'current-password');
      expect(passwordInput).toHaveAttribute('required');
    });

    it('エラー時に aria-invalid と aria-describedby が設定される', async () => {
      const user = userEvent.setup();
      render(
        <LoginForm
          onSubmit={mockOnSubmit}
          onGoogleLogin={mockOnGoogleLogin}
          isLoading={false}
        />
      );

      const submitButton = screen.getByRole('button', { name: 'ログイン' });
      await user.click(submitButton);

      await waitFor(() => {
        const emailInput = screen.getByLabelText('メールアドレス');
        expect(emailInput).toHaveAttribute('aria-invalid', 'true');
        expect(emailInput).toHaveAttribute('aria-describedby');
      });
    });
  });

  describe('パスワード表示/非表示', () => {
    it('パスワード表示トグルボタンで表示/非表示が切り替わる', async () => {
      const user = userEvent.setup();
      render(
        <LoginForm
          onSubmit={mockOnSubmit}
          onGoogleLogin={mockOnGoogleLogin}
          isLoading={false}
        />
      );

      const passwordInput = screen.getByLabelText('パスワード');
      expect(passwordInput).toHaveAttribute('type', 'password');

      const toggleButton = screen.getByRole('button', { name: 'パスワードを表示' });
      await user.click(toggleButton);

      expect(passwordInput).toHaveAttribute('type', 'text');
      expect(toggleButton).toHaveAccessibleName('パスワードを非表示');

      await user.click(toggleButton);
      expect(passwordInput).toHaveAttribute('type', 'password');
    });
  });
});