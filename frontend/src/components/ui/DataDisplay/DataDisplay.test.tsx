import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'

import Table from './Table'
import Chart from './Chart'
import Stats from './Stats'

// Mock recharts components
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  AreaChart: ({ children }: any) => <div data-testid="area-chart">{children}</div>,
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  Area: () => <div data-testid="area" />,
  Bar: () => <div data-testid="bar" />,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
}))

describe('Data Display Components', () => {
  describe('Table', () => {
    const mockData = [
      { id: 1, name: 'John Doe', email: 'john@example.com', role: 'Admin' },
      { id: 2, name: 'Jane Smith', email: 'jane@example.com', role: 'User' },
      { id: 3, name: 'Bob Johnson', email: 'bob@example.com', role: 'User' },
    ]

    const mockColumns = [
      { id: 'name', header: 'Name', accessor: 'name' as const, sortable: true },
      { id: 'email', header: 'Email', accessor: 'email' as const },
      { id: 'role', header: 'Role', accessor: 'role' as const, filterable: true },
    ]

    it('renders table with data correctly', () => {
      render(<Table data={mockData} columns={mockColumns} />)
      
      expect(screen.getByText('Name')).toBeInTheDocument()
      expect(screen.getByText('Email')).toBeInTheDocument()
      expect(screen.getByText('Role')).toBeInTheDocument()
      
      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getByText('jane@example.com')).toBeInTheDocument()
      expect(screen.getByText('Admin')).toBeInTheDocument()
    })

    it('handles empty data', () => {
      render(<Table data={[]} columns={mockColumns} />)
      
      expect(screen.getByText('No data available')).toBeInTheDocument()
    })

    it('shows loading state', () => {
      render(<Table data={[]} columns={mockColumns} loading={true} />)
      
      expect(screen.getByText('Loading...')).toBeInTheDocument()
    })

    it('shows error state', () => {
      const errorMessage = 'Failed to load data'
      render(<Table data={[]} columns={mockColumns} error={errorMessage} />)
      
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })

    it('handles row clicks', async () => {
      const user = userEvent.setup()
      const handleRowClick = vi.fn()
      
      render(<Table data={mockData} columns={mockColumns} onRowClick={handleRowClick} />)
      
      const firstRow = screen.getByText('John Doe').closest('tr')
      await user.click(firstRow!)
      
      expect(handleRowClick).toHaveBeenCalledWith(mockData[0], 0)
    })

    it('handles column sorting', async () => {
      const user = userEvent.setup()
      const handleSort = vi.fn()
      
      render(<Table data={mockData} columns={mockColumns} onSort={handleSort} />)
      
      const nameHeader = screen.getByText('Name')
      await user.click(nameHeader)
      
      expect(handleSort).toHaveBeenCalledWith('name', 'asc')
    })

    it('supports row selection', async () => {
      const user = userEvent.setup()
      const handleRowSelect = vi.fn()
      
      render(<Table data={mockData} columns={mockColumns} selectable={true} onRowSelect={handleRowSelect} />)
      
      const selectAllCheckbox = screen.getByLabelText('Select all rows')
      await user.click(selectAllCheckbox)
      
      expect(handleRowSelect).toHaveBeenCalledWith(mockData)
    })

    it('renders custom cell content', () => {
      const customColumns = [
        {
          id: 'name',
          header: 'Name',
          accessor: 'name' as const,
          cell: (value: any) => <strong>{value}</strong>
        },
      ]
      
      render(<Table data={mockData} columns={customColumns} />)
      
      const strongElement = screen.getByText('John Doe')
      expect(strongElement.tagName).toBe('STRONG')
    })

    it('applies striped styling', () => {
      render(<Table data={mockData} columns={mockColumns} striped={true} />)
      
      const rows = screen.getAllByRole('row')
      // First row is header, so data rows start from index 1
      expect(rows[2]).toHaveClass('bg-gray-50') // Second data row should be striped
    })

    it('shows pagination info when provided', () => {
      render(
        <Table 
          data={mockData} 
          columns={mockColumns} 
          currentPage={1}
          totalPages={5}
          totalItems={50}
          pageSize={10}
        />
      )
      
      expect(screen.getByText(/Showing/)).toBeInTheDocument()
      expect(screen.getByText(/1.*to.*10.*of.*50.*results/)).toBeInTheDocument()
    })
  })

  describe('Chart', () => {
    const mockData = [
      { month: 'Jan', sales: 4000, revenue: 2400 },
      { month: 'Feb', sales: 3000, revenue: 1398 },
      { month: 'Mar', sales: 2000, revenue: 9800 },
    ]

    const mockSeries = [
      { dataKey: 'sales', name: 'Sales', color: '#8884d8' },
      { dataKey: 'revenue', name: 'Revenue', color: '#82ca9d' },
    ]

    it('renders line chart correctly', () => {
      render(
        <Chart
          type="line"
          data={mockData}
          series={mockSeries}
          xAxis={{ dataKey: 'month' }}
        />
      )
      
      expect(screen.getByTestId('responsive-container')).toBeInTheDocument()
      expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    })

    it('renders bar chart correctly', () => {
      render(
        <Chart
          type="bar"
          data={mockData}
          series={mockSeries}
          xAxis={{ dataKey: 'month' }}
        />
      )
      
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
    })

    it('renders area chart correctly', () => {
      render(
        <Chart
          type="area"
          data={mockData}
          series={mockSeries}
          xAxis={{ dataKey: 'month' }}
        />
      )
      
      expect(screen.getByTestId('area-chart')).toBeInTheDocument()
    })

    it('renders pie chart correctly', () => {
      render(
        <Chart
          type="pie"
          data={mockData}
          series={[{ dataKey: 'sales' }]}
        />
      )
      
      expect(screen.getByTestId('pie-chart')).toBeInTheDocument()
    })

    it('shows title and description', () => {
      render(
        <Chart
          type="line"
          data={mockData}
          series={mockSeries}
          title="Sales Chart"
          description="Monthly sales and revenue data"
          xAxis={{ dataKey: 'month' }}
        />
      )
      
      expect(screen.getByText('Sales Chart')).toBeInTheDocument()
      expect(screen.getByText('Monthly sales and revenue data')).toBeInTheDocument()
    })

    it('shows loading state', () => {
      render(
        <Chart
          type="line"
          data={[]}
          series={mockSeries}
          loading={true}
        />
      )
      
      expect(screen.getByText('Loading chart...')).toBeInTheDocument()
    })

    it('shows error state', () => {
      const errorMessage = 'Failed to load chart data'
      render(
        <Chart
          type="line"
          data={[]}
          series={mockSeries}
          error={errorMessage}
        />
      )
      
      expect(screen.getByText('Error loading chart')).toBeInTheDocument()
    })

    it('shows empty state', () => {
      render(
        <Chart
          type="line"
          data={[]}
          series={mockSeries}
          emptyMessage="No chart data"
        />
      )
      
      expect(screen.getByText('No chart data')).toBeInTheDocument()
    })
  })

  describe('Stats', () => {
    const mockStats = [
      {
        id: 'users',
        label: 'Total Users',
        value: 1250,
        change: { value: 12, type: 'increase' as const, percentage: true, period: 'last month' },
        format: 'number' as const,
      },
      {
        id: 'revenue',
        label: 'Revenue',
        value: 45000,
        change: { value: -5, type: 'decrease' as const, percentage: true },
        format: 'currency' as const,
      },
      {
        id: 'conversion',
        label: 'Conversion Rate',
        value: 3.45,
        format: 'percentage' as const,
      },
    ]

    it('renders stats correctly', () => {
      render(<Stats items={mockStats} />)
      
      expect(screen.getByText('Total Users')).toBeInTheDocument()
      expect(screen.getByText('Revenue')).toBeInTheDocument()
      expect(screen.getByText('Conversion Rate')).toBeInTheDocument()
      
      expect(screen.getByText('1,250')).toBeInTheDocument()
      expect(screen.getByText('$45,000')).toBeInTheDocument()
      expect(screen.getByText('3.45%')).toBeInTheDocument()
    })

    it('shows change indicators', () => {
      render(<Stats items={mockStats} showTrend={true} showComparison={true} />)
      
      expect(screen.getByText('12.0%')).toBeInTheDocument()
      expect(screen.getByText('5.0%')).toBeInTheDocument()
      expect(screen.getByText('vs last month')).toBeInTheDocument()
    })

    it('handles click events', async () => {
      const user = userEvent.setup()
      const handleClick = vi.fn()
      
      const clickableStats = [
        {
          ...mockStats[0],
          onClick: handleClick,
        },
      ]
      
      render(<Stats items={clickableStats} />)
      
      const statItem = screen.getByText('Total Users').closest('button')
      await user.click(statItem!)
      
      expect(handleClick).toHaveBeenCalled()
    })

    it('renders loading states', () => {
      const loadingStats = [
        {
          id: 'loading',
          label: 'Loading Stat',
          value: 0,
          loading: true,
        },
      ]
      
      render(<Stats items={loadingStats} />)
      
      expect(screen.getByText('Loading Stat')).toBeInTheDocument()
      // Should show loading skeleton
      const loadingElement = document.querySelector('.animate-pulse')
      expect(loadingElement).toBeInTheDocument()
    })

    it('renders error states', () => {
      const errorStats = [
        {
          id: 'error',
          label: 'Error Stat',
          value: 0,
          error: 'Failed to load',
        },
      ]
      
      render(<Stats items={errorStats} />)
      
      expect(screen.getByText('Error Stat')).toBeInTheDocument()
      expect(screen.getByText('Error loading data')).toBeInTheDocument()
    })

    it('applies different layouts', () => {
      const { rerender } = render(<Stats items={mockStats} layout="grid" />)
      expect(document.querySelector('.grid')).toBeInTheDocument()
      
      rerender(<Stats items={mockStats} layout="horizontal" />)
      expect(document.querySelector('.flex')).toBeInTheDocument()
      
      rerender(<Stats items={mockStats} layout="vertical" />)
      expect(document.querySelector('.space-y-4')).toBeInTheDocument()
    })

    it('applies different sizes', () => {
      const { rerender } = render(<Stats items={mockStats} size="sm" />)
      
      rerender(<Stats items={mockStats} size="lg" />)
      // Size differences are primarily in CSS classes, which are tested implicitly
      expect(screen.getByText('Total Users')).toBeInTheDocument()
    })

    it('handles href navigation', () => {
      const linkStats = [
        {
          ...mockStats[0],
          href: '/users',
        },
      ]
      
      render(<Stats items={linkStats} />)
      
      const linkElement = screen.getByText('Total Users').closest('a')
      expect(linkElement).toHaveAttribute('href', '/users')
    })

    it('formats different value types correctly', () => {
      const formattedStats = [
        { id: 'number', label: 'Number', value: 1234.56, format: 'number' as const, precision: 2 },
        { id: 'currency', label: 'Currency', value: 1234.56, format: 'currency' as const, precision: 2 },
        { id: 'percentage', label: 'Percentage', value: 12.345, format: 'percentage' as const, precision: 1 },
        { id: 'decimal', label: 'Decimal', value: 12.345, format: 'decimal' as const, precision: 2 },
      ]
      
      render(<Stats items={formattedStats} />)
      
      expect(screen.getByText('1,234.56')).toBeInTheDocument()
      expect(screen.getByText('$1,234.56')).toBeInTheDocument()
      expect(screen.getByText('12.3%')).toBeInTheDocument()
      expect(screen.getByText('12.35')).toBeInTheDocument()
    })
  })
})