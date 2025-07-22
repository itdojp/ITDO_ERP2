import { render, screen } from '@testing-library/react';
import { DashboardPage } from './Dashboard';

describe('DashboardPage', () => {
  it('renders dashboard page', () => {
    render(<DashboardPage />);
    
    expect(screen.getByText('ITDO ERP - ダッシュボード')).toBeDefined();
    expect(screen.getByText('最近のアクティビティ')).toBeDefined();
    expect(screen.getByText('システムの最新の動向')).toBeDefined();
  });

  it('displays metrics cards', () => {
    render(<DashboardPage />);
    
    // Check metric cards
    expect(screen.getByText('総売上')).toBeDefined();
    expect(screen.getByText('注文数')).toBeDefined();
    expect(screen.getByText('商品数')).toBeDefined();
    expect(screen.getByText('ユーザー数')).toBeDefined();
    
    // Check values
    expect(screen.getByText('¥12,450,000')).toBeDefined();
    expect(screen.getByText('248件')).toBeDefined();
    expect(screen.getByText('156個')).toBeDefined();
    expect(screen.getByText('45名')).toBeDefined();
  });

  it('displays recent activity', () => {
    render(<DashboardPage />);
    
    expect(screen.getByText('新規注文: ThinkPad X1 Carbon × 3台')).toBeDefined();
    expect(screen.getByText('ユーザー登録: 佐藤 花子')).toBeDefined();
    expect(screen.getByText('在庫警告: USB-C ハブ (残り8個)')).toBeDefined();
  });
});