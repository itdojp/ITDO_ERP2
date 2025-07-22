import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { Login } from './Login';
import { useAuth } from '../../hooks/useAuth';

// useAuth フックをモック
jest.mock('../../hooks/useAuth');
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

// React Router のナビゲーションをモック
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// テストコンポーネントラッパー
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

// デフォルトの認証状態
const defaultAuthState = {
  user: null,
  tokens: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  login: jest.fn(),
  logout: jest.fn(),
  refreshAccessToken: jest.fn(),
  hasPermission: jest.fn(),
  hasRole: jest.fn(),
};

describe('Login Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue(defaultAuthState);
  });

  it('ログインフォームが正しくレンダリングされる', () => {
    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    expect(screen.getByRole('heading', { name: /ITDO ERP システム/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/ユーザー名/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/パスワード/i)).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: /ログイン状態を保持する/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /ログイン/i })).toBeInTheDocument();
  });

  it('デモアカウント情報が表示される', () => {
    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    expect(screen.getByText(/デモアカウント/i)).toBeInTheDocument();
    expect(screen.getByText('admin')).toBeInTheDocument();
    expect(screen.getByText('password')).toBeInTheDocument();
  });

  it('フォームバリデーションが正常に動作する', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    const submitButton = screen.getByRole('button', { name: /ログイン/i });
    
    // 空のフォームで送信
    await user.click(submitButton);
    
    expect(screen.getByText('ユーザー名を入力してください')).toBeInTheDocument();
    expect(screen.getByText('パスワードを入力してください')).toBeInTheDocument();
  });

  it('短いパスワードでバリデーションエラーが表示される', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    const passwordInput = screen.getByLabelText(/パスワード/i);
    const submitButton = screen.getByRole('button', { name: /ログイン/i });
    
    await user.type(passwordInput, '123');
    await user.click(submitButton);
    
    expect(screen.getByText('パスワードは6文字以上で入力してください')).toBeInTheDocument();
  });

  it('パスワード表示/非表示の切り替えができる', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    const passwordInput = screen.getByLabelText(/パスワード/i) as HTMLInputElement;
    const toggleButton = screen.getByRole('button', { name: '' }); // パスワード表示切り替えボタン
    
    // 初期状態では password タイプ
    expect(passwordInput.type).toBe('password');
    
    // 表示切り替え
    await user.click(toggleButton);
    expect(passwordInput.type).toBe('text');
    
    // 再度切り替え
    await user.click(toggleButton);
    expect(passwordInput.type).toBe('password');
  });

  it('有効なフォームデータでログインが実行される', async () => {
    const user = userEvent.setup();
    const mockLogin = jest.fn();
    
    mockUseAuth.mockReturnValue({
      ...defaultAuthState,
      login: mockLogin,
    });

    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    const usernameInput = screen.getByLabelText(/ユーザー名/i);
    const passwordInput = screen.getByLabelText(/パスワード/i);
    const rememberMeCheckbox = screen.getByRole('checkbox', { name: /ログイン状態を保持する/i });
    const submitButton = screen.getByRole('button', { name: /ログイン/i });
    
    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');
    await user.click(rememberMeCheckbox);
    await user.click(submitButton);
    
    expect(mockLogin).toHaveBeenCalledWith({
      username: 'testuser',
      password: 'password123',
      rememberMe: true,
    });
  });

  it('ローディング中は送信ボタンが無効化される', () => {
    mockUseAuth.mockReturnValue({
      ...defaultAuthState,
      isLoading: true,
    });

    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    const submitButton = screen.getByRole('button', { name: /ログイン中.../i });
    expect(submitButton).toBeDisabled();
    expect(screen.getByText('ログイン中...')).toBeInTheDocument();
  });

  it('エラーメッセージが表示される', () => {
    const errorMessage = 'ログインに失敗しました';
    
    mockUseAuth.mockReturnValue({
      ...defaultAuthState,
      error: errorMessage,
    });

    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    expect(screen.getByText('ログインエラー')).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('認証済みの場合はダッシュボードにリダイレクトされる', () => {
    mockUseAuth.mockReturnValue({
      ...defaultAuthState,
      isAuthenticated: true,
    });

    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
  });

  it('入力値変更時にエラーメッセージがクリアされる', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    const usernameInput = screen.getByLabelText(/ユーザー名/i);
    const submitButton = screen.getByRole('button', { name: /ログイン/i });
    
    // エラーを発生させる
    await user.click(submitButton);
    expect(screen.getByText('ユーザー名を入力してください')).toBeInTheDocument();
    
    // 入力値を変更
    await user.type(usernameInput, 'testuser');
    expect(screen.queryByText('ユーザー名を入力してください')).not.toBeInTheDocument();
  });

  it('パスワードを忘れた方のリンクが正しく表示される', () => {
    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    const forgotPasswordLink = screen.getByRole('link', { name: /パスワードを忘れた方/i });
    expect(forgotPasswordLink).toBeInTheDocument();
    expect(forgotPasswordLink).toHaveAttribute('href', '/forgot-password');
  });
});