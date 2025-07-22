import { render, screen } from '@testing-library/react';
import { UserListPage } from './UserList';

describe('UserListPage', () => {
  it('renders user management page', () => {
    render(<UserListPage />);
    
    expect(screen.getByText('ITDO ERP - ユーザー管理')).toBeDefined();
    expect(screen.getByText('ユーザー一覧')).toBeDefined();
    expect(screen.getByText('システムユーザーの一覧と管理')).toBeDefined();
  });

  it('displays user list table', () => {
    render(<UserListPage />);
    
    // Check table headers
    expect(screen.getByText('ユーザー名')).toBeDefined();
    expect(screen.getByText('メールアドレス')).toBeDefined();
    expect(screen.getByText('フルネーム')).toBeDefined();
    expect(screen.getByText('状態')).toBeDefined();
    
    // Check user data
    expect(screen.getByText('田中 太郎')).toBeDefined();
    expect(screen.getByText('tanaka@itdo.jp')).toBeDefined();
    expect(screen.getByText('佐藤 花子')).toBeDefined();
    expect(screen.getByText('山田 次郎')).toBeDefined();
  });
});