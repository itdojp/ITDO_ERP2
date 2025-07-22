import { render, screen } from '@testing-library/react';
import { MainLayout } from './MainLayout';

describe('MainLayout', () => {
  it('renders layout with navigation', () => {
    render(
      <MainLayout>
        <div>Test content</div>
      </MainLayout>
    );
    
    expect(screen.getByText('ITDO ERP')).toBeDefined();
    expect(screen.getByText('ダッシュボード')).toBeDefined();
    expect(screen.getByText('ユーザー管理')).toBeDefined();
    expect(screen.getByText('商品管理')).toBeDefined();
    expect(screen.getByText('Test content')).toBeDefined();
  });
});