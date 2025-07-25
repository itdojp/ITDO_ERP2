import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useFinancialStats, useFinancialDashboard, useSalesStats } from '../../hooks/useFinancial';
import { useSalesStats as useSalesStatsHook } from '../../hooks/useSales';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Button,
  IconButton,
  Stack,
  Chip,
  Avatar,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  Alert,
  Divider,
  Badge
} from '@mui/material';
import {
  AccountBalance as AccountingIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  AttachMoney as RevenueIcon,
  Receipt as ExpenseIcon,
  Assessment as ProfitIcon,
  CreditCard as CashFlowIcon,
  PieChart as PieChartIcon,
  BarChart as BarChartIcon,
  ShowChart as LineChartIcon,
  Download as ExportIcon,
  Print as PrintIcon,
  Email as EmailIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Schedule as PendingIcon,
  Business as BusinessIcon,
  AccountBalanceWallet as WalletIcon,
  MoneyOff as LossIcon,
  Savings as SavingsIcon,
  CurrencyExchange as ExchangeIcon,
  Calculate as CalculateIcon
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { apiClient } from '@/services/api';

interface FinancialMetrics {
  total_revenue: number;
  total_expenses: number;
  net_profit: number;
  gross_margin: number;
  operating_margin: number;
  current_ratio: number;
  quick_ratio: number;
  debt_to_equity: number;
  working_capital: number;
  cash_flow: number;
  accounts_receivable: number;
  accounts_payable: number;
  inventory_value: number;
  total_assets: number;
  total_liabilities: number;
  equity: number;
}

interface FinancialTrend {
  period: string;
  revenue: number;
  expenses: number;
  profit: number;
  cash_flow: number;
  assets: number;
  liabilities: number;
}

interface AccountBalance {
  account_id: number;
  account_code: string;
  account_name: string;
  account_type: 'asset' | 'liability' | 'equity' | 'revenue' | 'expense';
  balance: number;
  percentage_change: number;
  last_transaction_date: string;
}

interface CashFlowData {
  date: string;
  operating_cash_flow: number;
  investing_cash_flow: number;
  financing_cash_flow: number;
  net_cash_flow: number;
}

interface BudgetVsActual {
  category: string;
  budget_amount: number;
  actual_amount: number;
  variance: number;
  variance_percentage: number;
  status: 'over' | 'under' | 'on_track';
}

interface AgedReceivables {
  customer_name: string;
  total_amount: number;
  current: number;
  days_30: number;
  days_60: number;
  days_90: number;
  over_90: number;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

export const AccountingDashboardPage: React.FC = () => {
  const navigate = useNavigate();
  
  const [currentTab, setCurrentTab] = useState(0);
  const [dateRange, setDateRange] = useState('30'); // days
  const [selectedPeriod, setSelectedPeriod] = useState('monthly');
  const [comparisonPeriod, setComparisonPeriod] = useState('previous_year');

  // Calculate date range
  const dateRangeObj = useMemo(() => {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - parseInt(dateRange));
    
    return {
      start: startDate.toISOString().split('T')[0],
      end: endDate.toISOString().split('T')[0]
    };
  }, [dateRange]);

  // Fetch financial metrics
  const { data: metrics, isLoading: metricsLoading, refetch } = useQuery({
    queryKey: ['financial-metrics', dateRange],
    queryFn: async (): Promise<FinancialMetrics> => {
      // Mock data for rapid development
      await new Promise(resolve => setTimeout(resolve, 800));
      
      return {
        total_revenue: 2850000,
        total_expenses: 2100000,
        net_profit: 750000,
        gross_margin: 45.2,
        operating_margin: 26.3,
        current_ratio: 2.1,
        quick_ratio: 1.8,
        debt_to_equity: 0.35,
        working_capital: 1200000,
        cash_flow: 450000,
        accounts_receivable: 680000,
        accounts_payable: 320000,
        inventory_value: 890000,
        total_assets: 5200000,
        total_liabilities: 1800000,
        equity: 3400000
      };
    },
    refetchInterval: 300000, // Refresh every 5 minutes
  });

  // Fetch financial trends
  const { data: financialTrends } = useQuery({
    queryKey: ['financial-trends', selectedPeriod],
    queryFn: async (): Promise<FinancialTrend[]> => {
      // Mock data
      await new Promise(resolve => setTimeout(resolve, 600));
      
      return [
        { period: 'Jan', revenue: 2200000, expenses: 1650000, profit: 550000, cash_flow: 420000, assets: 4800000, liabilities: 1600000 },
        { period: 'Feb', revenue: 2350000, expenses: 1750000, profit: 600000, cash_flow: 380000, assets: 4950000, liabilities: 1650000 },
        { period: 'Mar', revenue: 2500000, expenses: 1850000, profit: 650000, cash_flow: 410000, assets: 5100000, liabilities: 1700000 },
        { period: 'Apr', revenue: 2650000, expenses: 1950000, profit: 700000, cash_flow: 450000, assets: 5200000, liabilities: 1750000 },
        { period: 'May', revenue: 2800000, expenses: 2000000, profit: 800000, cash_flow: 480000, assets: 5300000, liabilities: 1800000 },
        { period: 'Jun', revenue: 2850000, expenses: 2100000, profit: 750000, cash_flow: 450000, assets: 5200000, liabilities: 1800000 }
      ];
    },
  });

  // Fetch account balances
  const { data: accountBalances } = useQuery({
    queryKey: ['account-balances'],
    queryFn: async (): Promise<AccountBalance[]> => {
      // Mock data
      await new Promise(resolve => setTimeout(resolve, 500));
      
      return [
        { account_id: 1, account_code: '1000', account_name: 'Cash and Cash Equivalents', account_type: 'asset', balance: 850000, percentage_change: 12.5, last_transaction_date: '2024-01-20T14:30:00Z' },
        { account_id: 2, account_code: '1200', account_name: 'Accounts Receivable', account_type: 'asset', balance: 680000, percentage_change: -5.2, last_transaction_date: '2024-01-19T16:45:00Z' },
        { account_id: 3, account_code: '1300', account_name: 'Inventory', account_type: 'asset', balance: 890000, percentage_change: 8.7, last_transaction_date: '2024-01-20T11:20:00Z' },
        { account_id: 4, account_code: '2000', account_name: 'Accounts Payable', account_type: 'liability', balance: 320000, percentage_change: 15.3, last_transaction_date: '2024-01-20T09:15:00Z' },
        { account_id: 5, account_code: '4000', account_name: 'Sales Revenue', account_type: 'revenue', balance: 2850000, percentage_change: 18.2, last_transaction_date: '2024-01-20T17:00:00Z' },
        { account_id: 6, account_code: '5000', account_name: 'Cost of Goods Sold', account_type: 'expense', balance: 1560000, percentage_change: 12.8, last_transaction_date: '2024-01-20T15:30:00Z' }
      ];
    },
  });

  // Fetch cash flow data
  const { data: cashFlowData } = useQuery({
    queryKey: ['cash-flow-data'],
    queryFn: async (): Promise<CashFlowData[]> => {
      // Mock data
      await new Promise(resolve => setTimeout(resolve, 400));
      
      return [
        { date: 'Jan', operating_cash_flow: 420000, investing_cash_flow: -150000, financing_cash_flow: -80000, net_cash_flow: 190000 },
        { date: 'Feb', operating_cash_flow: 380000, investing_cash_flow: -200000, financing_cash_flow: 50000, net_cash_flow: 230000 },
        { date: 'Mar', operating_cash_flow: 410000, investing_cash_flow: -100000, financing_cash_flow: -30000, net_cash_flow: 280000 },
        { date: 'Apr', operating_cash_flow: 450000, investing_cash_flow: -180000, financing_cash_flow: 20000, net_cash_flow: 290000 },
        { date: 'May', operating_cash_flow: 480000, investing_cash_flow: -120000, financing_cash_flow: -40000, net_cash_flow: 320000 },
        { date: 'Jun', operating_cash_flow: 450000, investing_cash_flow: -90000, financing_cash_flow: -60000, net_cash_flow: 300000 }
      ];
    },
  });

  // Fetch budget vs actual
  const { data: budgetData } = useQuery({
    queryKey: ['budget-vs-actual'],
    queryFn: async (): Promise<BudgetVsActual[]> => {
      // Mock data
      await new Promise(resolve => setTimeout(resolve, 450));
      
      return [
        { category: 'Sales Revenue', budget_amount: 2700000, actual_amount: 2850000, variance: 150000, variance_percentage: 5.6, status: 'over' },
        { category: 'Cost of Sales', budget_amount: 1600000, actual_amount: 1560000, variance: -40000, variance_percentage: -2.5, status: 'under' },
        { category: 'Operating Expenses', budget_amount: 520000, actual_amount: 540000, variance: 20000, variance_percentage: 3.8, status: 'over' },
        { category: 'Marketing', budget_amount: 180000, actual_amount: 175000, variance: -5000, variance_percentage: -2.8, status: 'under' },
        { category: 'Administrative', budget_amount: 220000, actual_amount: 225000, variance: 5000, variance_percentage: 2.3, status: 'on_track' }
      ];
    },
  });

  // Process data for charts
  const accountTypeData = useMemo(() => {
    if (!accountBalances) return [];
    
    const grouped = accountBalances.reduce((acc, account) => {
      const type = account.account_type;
      if (!acc[type]) {
        acc[type] = { name: type, value: 0, count: 0 };
      }
      acc[type].value += Math.abs(account.balance);
      acc[type].count += 1;
      return acc;
    }, {} as any);
    
    return Object.values(grouped);
  }, [accountBalances]);

  const exportFinancialReport = (type: 'pdf' | 'excel') => {
    const params = new URLSearchParams({
      type,
      start_date: dateRangeObj.start,
      end_date: dateRangeObj.end,
      period: selectedPeriod
    });
    window.open(`/api/v1/accounting/export-report?${params}`, '_blank');
  };

  const getVarianceColor = (status: string) => {
    switch (status) {
      case 'over': return 'warning.main';
      case 'under': return 'success.main';
      default: return 'info.main';
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`;
  };

  return (
    <Box sx={{ maxWidth: 1400, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar sx={{ bgcolor: 'primary.main', width: 48, height: 48 }}>
              <AccountingIcon />
            </Avatar>
            Accounting Dashboard
          </Typography>
          
          <Stack direction="row" spacing={2}>
            <IconButton onClick={() => refetch()} disabled={metricsLoading}>
              <RefreshIcon />
            </IconButton>
            
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Period</InputLabel>
              <Select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                label="Period"
              >
                <MenuItem value="7">Last 7 days</MenuItem>
                <MenuItem value="30">Last 30 days</MenuItem>
                <MenuItem value="90">Last 90 days</MenuItem>
                <MenuItem value="365">Last year</MenuItem>
              </Select>
            </FormControl>
            
            <Button
              variant="outlined"
              startIcon={<EmailIcon />}
            >
              Email Report
            </Button>
            
            <Button
              variant="outlined"
              startIcon={<PrintIcon />}
            >
              Print
            </Button>
            
            <Button
              variant="contained"
              startIcon={<ExportIcon />}
              onClick={() => exportFinancialReport('pdf')}
            >
              Export
            </Button>
          </Stack>
        </Stack>

        {/* Date Range Display */}
        <Typography variant="body1" color="text.secondary">
          Financial data from {new Date(dateRangeObj.start).toLocaleDateString()} to {new Date(dateRangeObj.end).toLocaleDateString()}
        </Typography>
      </Paper>

      {/* Key Financial Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: 'success.main', width: 56, height: 56 }}>
                  <RevenueIcon />
                </Avatar>
                <Box flex={1}>
                  <Typography variant="h4" component="div">
                    {formatCurrency(metrics?.total_revenue || 0)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Revenue
                  </Typography>
                  <Stack direction="row" alignItems="center" spacing={1} mt={1}>
                    <TrendingUpIcon color="success" />
                    <Typography variant="caption" color="success.main">
                      +18.2%
                    </Typography>
                  </Stack>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: 'error.main', width: 56, height: 56 }}>
                  <ExpenseIcon />
                </Avatar>
                <Box flex={1}>
                  <Typography variant="h4" component="div">
                    {formatCurrency(metrics?.total_expenses || 0)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Expenses
                  </Typography>
                  <Stack direction="row" alignItems="center" spacing={1} mt={1}>
                    <TrendingUpIcon color="error" />
                    <Typography variant="caption" color="error.main">
                      +12.8%
                    </Typography>
                  </Stack>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: 'primary.main', width: 56, height: 56 }}>
                  <ProfitIcon />
                </Avatar>
                <Box flex={1}>
                  <Typography variant="h4" component="div">
                    {formatCurrency(metrics?.net_profit || 0)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Net Profit
                  </Typography>
                  <Stack direction="row" alignItems="center" spacing={1} mt={1}>
                    <TrendingUpIcon color="success" />
                    <Typography variant="caption" color="success.main">
                      +22.5%
                    </Typography>
                  </Stack>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: 'info.main', width: 56, height: 56 }}>
                  <CashFlowIcon />
                </Avatar>
                <Box flex={1}>
                  <Typography variant="h4" component="div">
                    {formatCurrency(metrics?.cash_flow || 0)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Cash Flow
                  </Typography>
                  <Stack direction="row" alignItems="center" spacing={1} mt={1}>
                    <TrendingUpIcon color="info" />
                    <Typography variant="caption" color="info.main">
                      +15.3%
                    </Typography>
                  </Stack>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Financial Ratios */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={2}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <CalculateIcon color="primary" sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h6">{metrics?.gross_margin?.toFixed(1) || '0.0'}%</Typography>
              <Typography variant="caption" color="text.secondary">Gross Margin</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={2}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <BusinessIcon color="info" sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h6">{metrics?.operating_margin?.toFixed(1) || '0.0'}%</Typography>
              <Typography variant="caption" color="text.secondary">Operating Margin</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={2}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <WalletIcon color="success" sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h6">{metrics?.current_ratio?.toFixed(1) || '0.0'}</Typography>
              <Typography variant="caption" color="text.secondary">Current Ratio</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={2}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <SavingsIcon color="warning" sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h6">{metrics?.quick_ratio?.toFixed(1) || '0.0'}</Typography>
              <Typography variant="caption" color="text.secondary">Quick Ratio</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={2}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <ExchangeIcon color="secondary" sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h6">{metrics?.debt_to_equity?.toFixed(2) || '0.00'}</Typography>
              <Typography variant="caption" color="text.secondary">Debt-to-Equity</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={2}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <CheckIcon color="success" sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h6">{formatCurrency(metrics?.working_capital || 0).replace('$', '$')}</Typography>
              <Typography variant="caption" color="text.secondary">Working Capital</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts and Analytics */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={currentTab}
          onChange={(_, newValue) => setCurrentTab(newValue)}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<LineChartIcon />} label="Revenue & Profit Trends" />
          <Tab icon={<BarChartIcon />} label="Cash Flow Analysis" />
          <Tab icon={<PieChartIcon />} label="Account Balances" />
          <Tab icon={<CalculateIcon />} label="Budget vs Actual" />
        </Tabs>
      </Paper>

      {/* Revenue & Profit Trends Tab */}
      <TabPanel value={currentTab} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12} lg={8}>
            <Card>
              <CardHeader 
                title="Financial Performance Trends"
                action={
                  <FormControl size="small" sx={{ minWidth: 100 }}>
                    <Select
                      value={selectedPeriod}
                      onChange={(e) => setSelectedPeriod(e.target.value)}
                    >
                      <MenuItem value="monthly">Monthly</MenuItem>
                      <MenuItem value="quarterly">Quarterly</MenuItem>
                      <MenuItem value="yearly">Yearly</MenuItem>
                    </Select>
                  </FormControl>
                }
              />
              <CardContent>
                {metricsLoading ? (
                  <LinearProgress />
                ) : financialTrends && financialTrends.length > 0 ? (
                  <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={financialTrends}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="period" />
                      <YAxis />
                      <Tooltip formatter={(value: number) => [formatCurrency(value), '']} />
                      <Legend />
                      <Line type="monotone" dataKey="revenue" stroke="#00C49F" strokeWidth={3} name="Revenue" />
                      <Line type="monotone" dataKey="expenses" stroke="#FF8042" strokeWidth={3} name="Expenses" />
                      <Line type="monotone" dataKey="profit" stroke="#0088FE" strokeWidth={3} name="Net Profit" />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <Alert severity="info">No financial trend data available</Alert>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} lg={4}>
            <Card>
              <CardHeader title="Financial Summary" />
              <CardContent>
                <Stack spacing={3}>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">Total Assets</Typography>
                    <Typography variant="h6">{formatCurrency(metrics?.total_assets || 0)}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">Total Liabilities</Typography>
                    <Typography variant="h6">{formatCurrency(metrics?.total_liabilities || 0)}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">Shareholders' Equity</Typography>
                    <Typography variant="h6" color="primary">{formatCurrency(metrics?.equity || 0)}</Typography>
                  </Box>
                  <Divider />
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">Accounts Receivable</Typography>
                    <Typography variant="h6">{formatCurrency(metrics?.accounts_receivable || 0)}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">Accounts Payable</Typography>
                    <Typography variant="h6">{formatCurrency(metrics?.accounts_payable || 0)}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">Inventory Value</Typography>
                    <Typography variant="h6">{formatCurrency(metrics?.inventory_value || 0)}</Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Cash Flow Analysis Tab */}
      <TabPanel value={currentTab} index={1}>
        <Card>
          <CardHeader title="Cash Flow Statement Analysis" />
          <CardContent>
            {cashFlowData && cashFlowData.length > 0 ? (
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={cashFlowData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip formatter={(value: number) => [formatCurrency(value), '']} />
                  <Legend />
                  <Bar dataKey="operating_cash_flow" fill="#00C49F" name="Operating Cash Flow" />
                  <Bar dataKey="investing_cash_flow" fill="#FF8042" name="Investing Cash Flow" />
                  <Bar dataKey="financing_cash_flow" fill="#8884D8" name="Financing Cash Flow" />
                  <Bar dataKey="net_cash_flow" fill="#0088FE" name="Net Cash Flow" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Alert severity="info">No cash flow data available</Alert>
            )}
          </CardContent>
        </Card>
      </TabPanel>

      {/* Account Balances Tab */}
      <TabPanel value={currentTab} index={2}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Account Balance Distribution" />
              <CardContent>
                {accountTypeData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={accountTypeData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={(entry) => `${entry.name}: ${formatCurrency(entry.value)}`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {accountTypeData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value: number) => [formatCurrency(value), 'Balance']} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <Alert severity="info">No account balance data available</Alert>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Key Account Balances" />
              <CardContent>
                <TableContainer sx={{ maxHeight: 300 }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell>Account</TableCell>
                        <TableCell align="right">Balance</TableCell>
                        <TableCell align="right">Change</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {accountBalances?.map((account) => (
                        <TableRow key={account.account_id}>
                          <TableCell>
                            <Box>
                              <Typography variant="body2" fontWeight="medium">
                                {account.account_name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {account.account_code}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" fontWeight="medium">
                              {formatCurrency(account.balance)}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography 
                              variant="body2" 
                              color={account.percentage_change >= 0 ? 'success.main' : 'error.main'}
                            >
                              {formatPercentage(account.percentage_change)}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Budget vs Actual Tab */}
      <TabPanel value={currentTab} index={3}>
        <Card>
          <CardHeader title="Budget vs Actual Performance" />
          <CardContent>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Category</TableCell>
                    <TableCell align="right">Budget</TableCell>
                    <TableCell align="right">Actual</TableCell>
                    <TableCell align="right">Variance</TableCell>
                    <TableCell align="right">Variance %</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {budgetData?.map((item, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {item.category}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {formatCurrency(item.budget_amount)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight="medium">
                          {formatCurrency(item.actual_amount)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography 
                          variant="body2" 
                          color={item.variance >= 0 ? 'success.main' : 'error.main'}
                        >
                          {formatCurrency(Math.abs(item.variance))}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography 
                          variant="body2" 
                          color={item.variance >= 0 ? 'success.main' : 'error.main'}
                        >
                          {formatPercentage(item.variance_percentage)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={item.status.replace('_', ' ')}
                          size="small"
                          color={
                            item.status === 'over' ? 'warning' :
                            item.status === 'under' ? 'success' :
                            'info'
                          }
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </TabPanel>
    </Box>
  );
};

export default AccountingDashboardPage;