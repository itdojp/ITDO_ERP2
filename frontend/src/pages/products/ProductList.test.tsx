import { render, screen } from '@testing-library/react';
import { ProductListPage } from './ProductList';

describe('ProductListPage', () => {
  it('renders product management page', () => {
    render(<ProductListPage />);
    
    expect(screen.getByText('ITDO ERP - 商品管理')).toBeDefined();
    expect(screen.getByText('商品一覧')).toBeDefined();
    expect(screen.getByText('商品・サービスの在庫管理')).toBeDefined();
  });

  it('displays product list table', () => {
    render(<ProductListPage />);
    
    // Check table headers
    expect(screen.getByText('商品コード')).toBeDefined();
    expect(screen.getByText('商品名')).toBeDefined();
    expect(screen.getByText('カテゴリ')).toBeDefined();
    expect(screen.getByText('価格')).toBeDefined();
    expect(screen.getByText('在庫数')).toBeDefined();
    expect(screen.getByText('状態')).toBeDefined();
    
    // Check product data
    expect(screen.getByText('ThinkPad X1 Carbon')).toBeDefined();
    expect(screen.getByText('LT-001')).toBeDefined();
    expect(screen.getByText('システム開発サービス')).toBeDefined();
    expect(screen.getByText('¥198,000')).toBeDefined();
  });
});