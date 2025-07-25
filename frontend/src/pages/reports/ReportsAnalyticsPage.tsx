import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
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
  Badge,
  Tooltip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton
} from '@mui/material';
import {
  Assessment as ReportsIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  PieChart as PieChartIcon,
  BarChart as BarChartIcon,
  ShowChart as LineChartIcon,
  Download as DownloadIcon,
  Print as PrintIcon,
  Email as EmailIcon,
  Schedule as ScheduleIcon,
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
  Dashboard as DashboardIcon,
  Receipt as InvoiceIcon,
  AccountBalance as FinanceIcon,
  Inventory as InventoryIcon,
  People as HRIcon,
  ShoppingCart as SalesIcon,
  Business as BusinessIcon,
  AttachMoney as MoneyIcon,
  DateRange as DateIcon,
  Category as CategoryIcon,
  Visibility as ViewIcon,
  GetApp as ExportIcon,
  Share as ShareIcon,
  Star as FavoriteIcon,
  StarBorder as NotFavoriteIcon
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
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { apiClient } from '@/services/api';

interface ReportTemplate {
  id: number;
  name: string;
  description: string;
  category: string;
  type: 'dashboard' | 'table' | 'chart' | 'pivot';
  is_favorite: boolean;
  is_scheduled: boolean;
  last_run: string;
  created_by: string;
  data_source: string;
  parameters: Record<string, any>;
}

interface ReportMetrics {
  total_reports: number;
  active_schedules: number;
  reports_this_month: number;
  avg_generation_time: number;
  most_popular_category: string;
  data_freshness_score: number;
}

interface DashboardWidget {
  id: number;
  title: string;
  type: 'kpi' | 'chart' | 'table' | 'gauge';
  size: 'small' | 'medium' | 'large';
  data: any;
  refreshInterval: number;
  position: { x: number; y: number };
}

interface BusinessIntelligenceData {
  revenue_trends: Array<{
    period: string;
    revenue: number;
    profit: number;
    growth_rate: number;
  }>;
  department_performance: Array<{
    department: string;
    revenue: number;
    expenses: number;
    profit_margin: number;
    employee_count: number;
  }>;
  customer_analytics: Array<{
    segment: string;
    customer_count: number;
    revenue: number;
    avg_order_value: number;
    retention_rate: number;
  }>;
  product_performance: Array<{
    category: string;
    units_sold: number;
    revenue: number;
    profit_margin: number;
    inventory_turnover: number;
  }>;
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

export const ReportsAnalyticsPage: React.FC = () => {
  const navigate = useNavigate();
  
  const [currentTab, setCurrentTab] = useState(0);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [dateRange, setDateRange] = useState('30');
  const [reportFilters, setReportFilters] = useState({
    search: '',
    category: '',
    type: '',
    is_favorite: false
  });

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

  // Mock report templates
  const mockReports: ReportTemplate[] = [
    {
      id: 1,
      name: 'Monthly Financial Summary',
      description: 'Comprehensive monthly financial performance overview with P&L analysis',
      category: 'Financial',
      type: 'dashboard',
      is_favorite: true,
      is_scheduled: true,
      last_run: '2024-01-20T09:00:00Z',
      created_by: 'Finance Team',
      data_source: 'Accounting System',
      parameters: { period: 'monthly', currency: 'USD' }
    },
    {
      id: 2,
      name: 'Sales Performance Analytics',
      description: 'Detailed sales metrics, trends, and customer segmentation analysis',
      category: 'Sales',
      type: 'chart',
      is_favorite: true,
      is_scheduled: false,
      last_run: '2024-01-19T14:30:00Z',
      created_by: 'Sales Manager',
      data_source: 'CRM System',
      parameters: { include_forecasts: true, segment_by: 'region' }
    },
    {
      id: 3,
      name: 'Inventory Turnover Report',
      description: 'Product inventory analysis with turnover rates and stock optimization',
      category: 'Inventory',
      type: 'table',
      is_favorite: false,
      is_scheduled: true,
      last_run: '2024-01-18T11:15:00Z',
      created_by: 'Inventory Manager',
      data_source: 'Warehouse System',
      parameters: { include_abc_analysis: true, min_turnover: 2.0 }
    },
    {
      id: 4,
      name: 'Employee Performance Dashboard',
      description: 'HR metrics including productivity, engagement, and performance indicators',
      category: 'HR',
      type: 'dashboard',
      is_favorite: false,
      is_scheduled: false,
      last_run: '2024-01-17T16:45:00Z',
      created_by: 'HR Director',
      data_source: 'HRIS',
      parameters: { include_satisfaction: true, period: 'quarterly' }
    },
    {
      id: 5,
      name: 'Customer Acquisition Cost Analysis',
      description: 'Marketing ROI and customer acquisition cost breakdown by channel',
      category: 'Marketing',
      type: 'chart',
      is_favorite: true,
      is_scheduled: true,
      last_run: '2024-01-20T08:30:00Z',
      created_by: 'Marketing Director',
      data_source: 'Marketing Automation',
      parameters: { channels: 'all', include_ltv: true }
    },
    {
      id: 6,
      name: 'Operational Efficiency Report',
      description: 'Process efficiency metrics and operational KPIs across departments',
      category: 'Operations',
      type: 'pivot',
      is_favorite: false,
      is_scheduled: false,
      last_run: '2024-01-16T13:20:00Z',
      created_by: 'Operations Manager',
      data_source: 'ERP System',
      parameters: { include_benchmarks: true, granularity: 'weekly' }
    }
  ];

  // Fetch reports data
  const { data: reportsData, isLoading: reportsLoading, refetch } = useQuery({
    queryKey: ['reports', reportFilters],
    queryFn: async () => {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 600));
      
      // Filter mock data
      let filteredReports = mockReports;
      
      if (reportFilters.search) {
        const searchLower = reportFilters.search.toLowerCase();
        filteredReports = filteredReports.filter(report => 
          report.name.toLowerCase().includes(searchLower) ||
          report.description.toLowerCase().includes(searchLower)
        );
      }
      
      if (reportFilters.category && reportFilters.category !== 'all') {
        filteredReports = filteredReports.filter(report => report.category === reportFilters.category);
      }
      
      if (reportFilters.is_favorite) {
        filteredReports = filteredReports.filter(report => report.is_favorite);
      }
      
      // Calculate metrics
      const metrics: ReportMetrics = {
        total_reports: mockReports.length,
        active_schedules: mockReports.filter(r => r.is_scheduled).length,
        reports_this_month: 156,
        avg_generation_time: 4.2,
        most_popular_category: 'Financial',
        data_freshness_score: 94.5
      };
      
      return {
        reports: filteredReports,
        metrics
      };
    },
  });

  // Fetch business intelligence data
  const { data: biData } = useQuery({
    queryKey: ['business-intelligence', dateRange],
    queryFn: async (): Promise<BusinessIntelligenceData> => {
      // Mock BI data
      await new Promise(resolve => setTimeout(resolve, 800));
      
      return {
        revenue_trends: [
          { period: 'Jan', revenue: 285000, profit: 71250, growth_rate: 8.5 },
          { period: 'Feb', revenue: 295000, profit: 73750, growth_rate: 3.5 },
          { period: 'Mar', revenue: 310000, profit: 77500, growth_rate: 5.1 },
          { period: 'Apr', revenue: 325000, profit: 81250, growth_rate: 4.8 },
          { period: 'May', revenue: 340000, profit: 85000, growth_rate: 4.6 },
          { period: 'Jun', revenue: 355000, profit: 88750, growth_rate: 4.4 }
        ],
        department_performance: [
          { department: 'Sales', revenue: 890000, expenses: 267000, profit_margin: 70.0, employee_count: 12 },
          { department: 'Marketing', revenue: 156000, expenses: 124800, profit_margin: 20.0, employee_count: 8 },
          { department: 'Engineering', revenue: 420000, expenses: 336000, profit_margin: 20.0, employee_count: 15 },
          { department: 'Operations', revenue: 234000, expenses: 187200, profit_margin: 20.0, employee_count: 10 }
        ],
        customer_analytics: [
          { segment: 'Enterprise', customer_count: 45, revenue: 756000, avg_order_value: 16800, retention_rate: 95.5 },
          { segment: 'Mid-Market', customer_count: 128, revenue: 512000, avg_order_value: 4000, retention_rate: 87.3 },
          { segment: 'Small Business', customer_count: 340, revenue: 340000, avg_order_value: 1000, retention_rate: 76.8 },
          { segment: 'Startup', customer_count: 156, revenue: 93600, avg_order_value: 600, retention_rate: 68.2 }
        ],
        product_performance: [
          { category: 'Software Licenses', units_sold: 245, revenue: 490000, profit_margin: 85.0, inventory_turnover: 12.5 },
          { category: 'Hardware', units_sold: 156, revenue: 312000, profit_margin: 35.0, inventory_turnover: 4.2 },
          { category: 'Services', units_sold: 89, revenue: 445000, profit_margin: 65.0, inventory_turnover: 24.0 },
          { category: 'Support', units_sold: 320, revenue: 160000, profit_margin: 75.0, inventory_turnover: 52.0 }
        ]
      };
    },
  });

  // Event handlers
  const handleRunReport = (reportId: number) => {
    console.log('Running report:', reportId);
    // Implement report generation
  };

  const handleScheduleReport = (reportId: number) => {
    console.log('Scheduling report:', reportId);
    // Implement report scheduling
  };

  const handleFavoriteToggle = (reportId: number) => {
    console.log('Toggling favorite for report:', reportId);
    // Implement favorite toggle
  };

  const handleExportReport = (reportId: number, format: string) => {
    console.log('Exporting report:', reportId, 'as', format);
    // Implement export functionality
  };

  const handleCreateReport = () => {
    navigate('/reports/builder');
  };

  const getCategoryIcon = (category: string) => {
    const icons = {
      'Financial': <FinanceIcon />,
      'Sales': <SalesIcon />,
      'Inventory': <InventoryIcon />,
      'HR': <HRIcon />,
      'Marketing': <BusinessIcon />,
      'Operations': <DashboardIcon />
    };
    return icons[category as keyof typeof icons] || <ReportsIcon />;
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
              <ReportsIcon />
            </Avatar>
            Reports & Analytics Center
          </Typography>
          
          <Stack direction="row" spacing={2}>
            <IconButton onClick={() => refetch()} disabled={reportsLoading}>
              <RefreshIcon />
            </IconButton>
            
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Date Range</InputLabel>
              <Select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                label="Date Range"
              >
                <MenuItem value="7">Last 7 days</MenuItem>
                <MenuItem value="30">Last 30 days</MenuItem>
                <MenuItem value="90">Last 90 days</MenuItem>
                <MenuItem value="365">Last year</MenuItem>
              </Select>
            </FormControl>
            
            <Button
              variant="outlined"
              startIcon={<ScheduleIcon />}
            >
              Scheduled Reports
            </Button>
            
            <Button
              variant="contained"
              startIcon={<ReportsIcon />}
              onClick={handleCreateReport}
              size="large"
            >
              Create Report
            </Button>
          </Stack>
        </Stack>

        {/* Quick Metrics */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={2}>
            <Card sx={{ bgcolor: 'primary.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                  <ReportsIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{reportsData?.metrics.total_reports || 0}</Typography>
                  <Typography variant="caption" color="text.secondary">Total Reports</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2}>
            <Card sx={{ bgcolor: 'success.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                  <ScheduleIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{reportsData?.metrics.active_schedules || 0}</Typography>
                  <Typography variant="caption" color="text.secondary">Scheduled</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2}>
            <Card sx={{ bgcolor: 'info.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                  <TrendingUpIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{reportsData?.metrics.reports_this_month || 0}</Typography>
                  <Typography variant="caption" color="text.secondary">This Month</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2}>
            <Card sx={{ bgcolor: 'warning.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'warning.main', mr: 2 }}>
                  <DateIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{reportsData?.metrics.avg_generation_time?.toFixed(1) || '0.0'}s</Typography>
                  <Typography variant="caption" color="text.secondary">Avg Gen Time</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2}>
            <Card sx={{ bgcolor: 'error.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'error.main', mr: 2 }}>
                  <FilterIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{reportsData?.metrics.data_freshness_score?.toFixed(1) || '0.0'}%</Typography>
                  <Typography variant="caption" color="text.secondary">Data Freshness</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2}>
            <Card sx={{ bgcolor: 'secondary.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'secondary.main', mr: 2 }}>
                  <CategoryIcon />
                </Avatar>
                <Box>
                  <Typography variant="body2" fontWeight="medium">{reportsData?.metrics.most_popular_category || 'N/A'}</Typography>
                  <Typography variant="caption" color="text.secondary">Most Popular</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Main Content Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={currentTab}
          onChange={(_, newValue) => setCurrentTab(newValue)}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<ReportsIcon />} label="Report Library" />
          <Tab icon={<DashboardIcon />} label="Executive Dashboard" />
          <Tab icon={<BarChartIcon />} label="Business Intelligence" />
          <Tab icon={<ScheduleIcon />} label="Scheduled Reports" />
        </Tabs>
      </Paper>

      {/* Report Library Tab */}
      <TabPanel value={currentTab} index={0}>
        <Grid container spacing={3}>
          {/* Filter Panel */}
          <Grid item xs={12} md={3}>
            <Card>
              <CardHeader title="Report Filters" />
              <CardContent>
                <Stack spacing={3}>
                  <TextField
                    label="Search Reports"
                    placeholder="Search by name or description..."
                    value={reportFilters.search}
                    onChange={(e) => setReportFilters(prev => ({ ...prev, search: e.target.value }))}
                    fullWidth
                    size="small"
                  />
                  
                  <FormControl fullWidth size="small">
                    <InputLabel>Category</InputLabel>
                    <Select
                      value={reportFilters.category}
                      onChange={(e) => setReportFilters(prev => ({ ...prev, category: e.target.value }))}
                      label="Category"
                    >
                      <MenuItem value="">All Categories</MenuItem>
                      <MenuItem value="Financial">Financial</MenuItem>
                      <MenuItem value="Sales">Sales</MenuItem>
                      <MenuItem value="Inventory">Inventory</MenuItem>
                      <MenuItem value="HR">Human Resources</MenuItem>
                      <MenuItem value="Marketing">Marketing</MenuItem>
                      <MenuItem value="Operations">Operations</MenuItem>
                    </Select>
                  </FormControl>
                  
                  <FormControl fullWidth size="small">
                    <InputLabel>Report Type</InputLabel>
                    <Select
                      value={reportFilters.type}
                      onChange={(e) => setReportFilters(prev => ({ ...prev, type: e.target.value }))}
                      label="Report Type"
                    >
                      <MenuItem value="">All Types</MenuItem>
                      <MenuItem value="dashboard">Dashboard</MenuItem>
                      <MenuItem value="table">Table</MenuItem>
                      <MenuItem value="chart">Chart</MenuItem>
                      <MenuItem value="pivot">Pivot Table</MenuItem>
                    </Select>
                  </FormControl>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          {/* Reports Grid */}
          <Grid item xs={12} md={9}>
            <Grid container spacing={3}>
              {reportsData?.reports.map((report) => (
                <Grid item xs={12} md={6} lg={4} key={report.id}>
                  <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                    <CardHeader
                      avatar={
                        <Avatar sx={{ bgcolor: 'primary.main' }}>
                          {getCategoryIcon(report.category)}
                        </Avatar>
                      }
                      title={
                        <Typography variant="h6" noWrap>
                          {report.name}
                        </Typography>
                      }
                      subheader={
                        <Stack direction="row" spacing={1} mt={1}>
                          <Chip label={report.category} size="small" color="primary" variant="outlined" />
                          <Chip label={report.type} size="small" variant="outlined" />
                          {report.is_scheduled && <Chip label="Scheduled" size="small" color="success" />}
                        </Stack>
                      }
                      action={
                        <IconButton onClick={() => handleFavoriteToggle(report.id)}>
                          {report.is_favorite ? <FavoriteIcon color="warning" /> : <NotFavoriteIcon />}
                        </IconButton>
                      }
                    />
                    <CardContent sx={{ flexGrow: 1 }}>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {report.description}
                      </Typography>
                      <Stack spacing={1}>
                        <Typography variant="caption" color="text.secondary">
                          <strong>Data Source:</strong> {report.data_source}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          <strong>Last Run:</strong> {new Date(report.last_run).toLocaleString()}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          <strong>Created By:</strong> {report.created_by}
                        </Typography>
                      </Stack>
                    </CardContent>
                    <CardContent sx={{ pt: 0 }}>
                      <Stack direction="row" spacing={1}>
                        <Button
                          variant="contained"
                          size="small"
                          startIcon={<ViewIcon />}
                          onClick={() => handleRunReport(report.id)}
                          fullWidth
                        >
                          Run
                        </Button>
                        <Button
                          variant="outlined"
                          size="small"
                          startIcon={<DownloadIcon />}
                          onClick={() => handleExportReport(report.id, 'pdf')}
                        >
                          Export
                        </Button>
                        {!report.is_scheduled && (
                          <Button
                            variant="outlined"
                            size="small"
                            startIcon={<ScheduleIcon />}
                            onClick={() => handleScheduleReport(report.id)}
                          >
                            Schedule
                          </Button>
                        )}
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Executive Dashboard Tab */}
      <TabPanel value={currentTab} index={1}>
        <Grid container spacing={3}>
          {/* Revenue Trends */}
          <Grid item xs={12} lg={8}>
            <Card>
              <CardHeader title="Revenue & Profit Trends" />
              <CardContent>
                {biData?.revenue_trends ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={biData.revenue_trends}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="period" />
                      <YAxis />
                      <RechartsTooltip formatter={(value: number) => [formatCurrency(value), '']} />
                      <Legend />
                      <Line type="monotone" dataKey="revenue" stroke="#0088FE" strokeWidth={3} name="Revenue" />
                      <Line type="monotone" dataKey="profit" stroke="#00C49F" strokeWidth={3} name="Profit" />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <LinearProgress />
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Key Metrics Summary */}
          <Grid item xs={12} lg={4}>
            <Card>
              <CardHeader title="Key Performance Indicators" />
              <CardContent>
                <Stack spacing={3}>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">Total Revenue</Typography>
                    <Typography variant="h5" color="primary">
                      {formatCurrency(biData?.revenue_trends.reduce((sum, item) => sum + item.revenue, 0) || 0)}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">Total Profit</Typography>
                    <Typography variant="h5" color="success.main">
                      {formatCurrency(biData?.revenue_trends.reduce((sum, item) => sum + item.profit, 0) || 0)}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">Average Growth Rate</Typography>
                    <Typography variant="h5" color="info.main">
                      {biData?.revenue_trends.reduce((sum, item) => sum + item.growth_rate, 0) / (biData?.revenue_trends.length || 1) || 0}%
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          {/* Department Performance */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Department Performance" />
              <CardContent>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Department</TableCell>
                        <TableCell align="right">Revenue</TableCell>
                        <TableCell align="right">Profit Margin</TableCell>
                        <TableCell align="right">Employees</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {biData?.department_performance.map((dept) => (
                        <TableRow key={dept.department}>
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium">
                              {dept.department}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2">
                              {formatCurrency(dept.revenue)}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" color="success.main">
                              {dept.profit_margin.toFixed(1)}%
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2">
                              {dept.employee_count}
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

          {/* Customer Segments */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Customer Segment Analysis" />
              <CardContent>
                {biData?.customer_analytics ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                      <Pie
                        data={biData.customer_analytics}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={(entry) => `${entry.segment}: ${formatCurrency(entry.revenue)}`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="revenue"
                      >
                        {biData.customer_analytics.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <RechartsTooltip formatter={(value: number) => [formatCurrency(value), 'Revenue']} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <LinearProgress />
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Business Intelligence Tab */}
      <TabPanel value={currentTab} index={2}>
        <Grid container spacing={3}>
          {/* Product Performance */}
          <Grid item xs={12}>
            <Card>
              <CardHeader title="Product Category Performance Analysis" />
              <CardContent>
                {biData?.product_performance ? (
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={biData.product_performance}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="category" />
                      <YAxis yAxisId="left" />
                      <YAxis yAxisId="right" orientation="right" />
                      <RechartsTooltip />
                      <Legend />
                      <Bar yAxisId="left" dataKey="revenue" fill="#0088FE" name="Revenue ($)" />
                      <Bar yAxisId="left" dataKey="units_sold" fill="#00C49F" name="Units Sold" />
                      <Bar yAxisId="right" dataKey="profit_margin" fill="#FFBB28" name="Profit Margin (%)" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <LinearProgress />
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Advanced Analytics Summary */}
          <Grid item xs={12}>
            <Card>
              <CardHeader title="Advanced Business Intelligence Insights" />
              <CardContent>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={4}>
                    <Box textAlign="center">
                      <Avatar sx={{ bgcolor: 'success.main', width: 60, height: 60, mx: 'auto', mb: 2 }}>
                        <TrendingUpIcon />
                      </Avatar>
                      <Typography variant="h4" color="success.main">
                        {formatPercentage(8.2)}
                      </Typography>
                      <Typography variant="subtitle1" gutterBottom>
                        Revenue Growth
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Consistent growth across all quarters with strong Q2 performance
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Box textAlign="center">
                      <Avatar sx={{ bgcolor: 'primary.main', width: 60, height: 60, mx: 'auto', mb: 2 }}>
                        <MoneyIcon />
                      </Avatar>
                      <Typography variant="h4" color="primary.main">
                        {formatCurrency(4250)}
                      </Typography>
                      <Typography variant="subtitle1" gutterBottom>
                        Avg Customer LTV
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Lifetime value increased by 15% with improved retention strategies
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Box textAlign="center">
                      <Avatar sx={{ bgcolor: 'warning.main', width: 60, height: 60, mx: 'auto', mb: 2 }}>
                        <CategoryIcon />
                      </Avatar>
                      <Typography variant="h4" color="warning.main">
                        7.2x
                      </Typography>
                      <Typography variant="subtitle1" gutterBottom>
                        Inventory Turnover
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Optimized inventory management resulting in improved cash flow
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Scheduled Reports Tab */}
      <TabPanel value={currentTab} index={3}>
        <Card>
          <CardHeader 
            title="Scheduled Reports Management"
            action={
              <Button startIcon={<ScheduleIcon />} variant="contained">
                Create Schedule
              </Button>
            }
          />
          <CardContent>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Report Name</TableCell>
                    <TableCell>Category</TableCell>
                    <TableCell>Frequency</TableCell>
                    <TableCell>Next Run</TableCell>
                    <TableCell>Recipients</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {reportsData?.reports.filter(r => r.is_scheduled).map((report) => (
                    <TableRow key={report.id}>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {report.name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={report.category} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">Weekly</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toLocaleDateString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">5 recipients</Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label="Active" size="small" color="success" />
                      </TableCell>
                      <TableCell>
                        <Stack direction="row" spacing={1}>
                          <Tooltip title="Edit Schedule">
                            <IconButton size="small">
                              <ReportsIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Run Now">
                            <IconButton size="small">
                              <ViewIcon />
                            </IconButton>
                          </Tooltip>
                        </Stack>
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

export default ReportsAnalyticsPage;