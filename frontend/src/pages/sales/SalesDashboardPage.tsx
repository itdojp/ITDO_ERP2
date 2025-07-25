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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Tabs,
  Tab,
  Alert,
  Divider
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  AttachMoney as MoneyIcon,
  Receipt as OrderIcon,
  Person as CustomerIcon,
  Inventory as ProductIcon,
  DateRange as DateIcon,
  Assessment as ReportIcon,
  Refresh as RefreshIcon,
  Download as ExportIcon,
  Email as EmailIcon,
  Schedule as ScheduleIcon,
  Warning as WarningIcon,
  CheckCircle as SuccessIcon,
  PendingActions as PendingIcon,
  LocalShipping as ShippingIcon,
  Cancel as CancelledIcon,
  StarRate as TopIcon,
  BusinessCenter as DealIcon
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

interface SalesMetrics {
  total_revenue: number;
  total_orders: number;
  avg_order_value: number;
  new_customers: number;
  revenue_growth: number;
  orders_growth: number;
  customer_growth: number;
  conversion_rate: number;
  pending_orders: number;
  shipped_orders: number;
  delivered_orders: number;
  cancelled_orders: number;
}

interface SalesTrend {
  date: string;
  revenue: number;
  orders: number;
  new_customers: number;
}

interface TopProduct {
  product_id: number;
  product_name: string;
  product_code: string;
  quantity_sold: number;
  revenue: number;
  profit_margin: number;
}

interface TopCustomer {
  customer_id: number;
  customer_name: string;
  total_orders: number;
  total_spent: number;
  last_order_date: string;
}

interface RecentOrder {
  id: number;
  order_number: string;
  customer_name: string;
  order_date: string;
  status: string;
  total_amount: number;
  items_count: number;
}

interface SalesTarget {
  period: string;
  target_revenue: number;
  actual_revenue: number;
  achievement_rate: number;
  target_orders: number;
  actual_orders: number;
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

export const SalesDashboardPage: React.FC = () => {
  const navigate = useNavigate();
  
  const [currentTab, setCurrentTab] = useState(0);
  const [dateRange, setDateRange] = useState('30'); // days
  const [selectedPeriod, setSelectedPeriod] = useState('daily');

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

  // Fetch sales metrics
  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['sales-metrics', dateRange],
    queryFn: async (): Promise<SalesMetrics> => {
      const params = new URLSearchParams({
        start_date: dateRangeObj.start,
        end_date: dateRangeObj.end
      });
      const response = await apiClient.get(`/api/v1/sales/metrics?${params}`);
      return response.data || {
        total_revenue: 0,
        total_orders: 0,
        avg_order_value: 0,
        new_customers: 0,
        revenue_growth: 0,
        orders_growth: 0,
        customer_growth: 0,
        conversion_rate: 0,
        pending_orders: 0,
        shipped_orders: 0,
        delivered_orders: 0,
        cancelled_orders: 0
      };
    },
    refetchInterval: 300000, // Refresh every 5 minutes
  });

  // Fetch sales trends
  const { data: salesTrends } = useQuery({
    queryKey: ['sales-trends', dateRange, selectedPeriod],
    queryFn: async (): Promise<SalesTrend[]> => {
      const params = new URLSearchParams({
        start_date: dateRangeObj.start,
        end_date: dateRangeObj.end,
        period: selectedPeriod
      });
      const response = await apiClient.get(`/api/v1/sales/trends?${params}`);
      return response.data || [];
    },
  });

  // Fetch top products
  const { data: topProducts } = useQuery({
    queryKey: ['top-products', dateRange],
    queryFn: async (): Promise<TopProduct[]> => {
      const params = new URLSearchParams({
        start_date: dateRangeObj.start,
        end_date: dateRangeObj.end,
        limit: '10'
      });
      const response = await apiClient.get(`/api/v1/sales/top-products?${params}`);
      return response.data || [];
    },
  });

  // Fetch top customers
  const { data: topCustomers } = useQuery({
    queryKey: ['top-customers', dateRange],
    queryFn: async (): Promise<TopCustomer[]> => {
      const params = new URLSearchParams({
        start_date: dateRangeObj.start,
        end_date: dateRangeObj.end,
        limit: '10'
      });
      const response = await apiClient.get(`/api/v1/sales/top-customers?${params}`);
      return response.data || [];
    },
  });

  // Fetch recent orders
  const { data: recentOrders } = useQuery({
    queryKey: ['recent-orders'],
    queryFn: async (): Promise<RecentOrder[]> => {
      const response = await apiClient.get('/api/v1/sales-orders?limit=10&sort=date_desc');
      return response.data?.orders || [];
    },
    refetchInterval: 60000, // Refresh every minute
  });

  // Fetch sales targets
  const { data: salesTargets } = useQuery({
    queryKey: ['sales-targets', dateRange],
    queryFn: async (): Promise<SalesTarget[]> => {
      const response = await apiClient.get('/api/v1/sales/targets');
      return response.data || [];
    },
  });

  // Process order status data for pie chart
  const orderStatusData = useMemo(() => {
    if (!metrics) return [];
    
    return [
      { name: 'Pending', value: metrics.pending_orders, color: '#FFA726' },
      { name: 'Shipped', value: metrics.shipped_orders, color: '#42A5F5' },
      { name: 'Delivered', value: metrics.delivered_orders, color: '#66BB6A' },
      { name: 'Cancelled', value: metrics.cancelled_orders, color: '#EF5350' }
    ].filter(item => item.value > 0);
  }, [metrics]);

  const exportReport = (type: 'pdf' | 'excel') => {
    const params = new URLSearchParams({
      type,
      start_date: dateRangeObj.start,
      end_date: dateRangeObj.end
    });
    window.open(`/api/v1/sales/export-report?${params}`, '_blank');
  };

  const getGrowthIcon = (growth: number) => {
    if (growth > 0) {
      return <TrendingUpIcon color="success" />;
    } else if (growth < 0) {
      return <TrendingDownIcon color="error" />;
    }
    return null;
  };

  const getGrowthColor = (growth: number) => {
    if (growth > 0) return 'success.main';
    if (growth < 0) return 'error.main';
    return 'text.secondary';
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" component="h1">
            Sales Dashboard
          </Typography>
          
          <Stack direction="row" spacing={2}>
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
              startIcon={<ScheduleIcon />}
            >
              Schedule
            </Button>
            
            <Button
              variant="outlined"
              startIcon={<EmailIcon />}
            >
              Email Report
            </Button>
            
            <Button
              variant="contained"
              startIcon={<ExportIcon />}
              onClick={() => exportReport('pdf')}
            >
              Export
            </Button>
          </Stack>
        </Stack>

        {/* Date Range Display */}
        <Typography variant="body1" color="text.secondary">
          Showing data from {new Date(dateRangeObj.start).toLocaleDateString()} to {new Date(dateRangeObj.end).toLocaleDateString()}
        </Typography>
      </Paper>

      {/* Key Metrics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: 'success.main', width: 56, height: 56 }}>
                  <MoneyIcon />
                </Avatar>
                <Box flex={1}>
                  <Typography variant="h4" component="div">
                    ${metrics?.total_revenue?.toFixed(0) || '0'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Revenue
                  </Typography>
                  <Stack direction="row" alignItems="center" spacing={1} mt={1}>
                    {getGrowthIcon(metrics?.revenue_growth || 0)}
                    <Typography 
                      variant="caption" 
                      color={getGrowthColor(metrics?.revenue_growth || 0)}
                    >
                      {metrics?.revenue_growth > 0 ? '+' : ''}{metrics?.revenue_growth?.toFixed(1) || '0'}%
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
                  <OrderIcon />
                </Avatar>
                <Box flex={1}>
                  <Typography variant="h4" component="div">
                    {metrics?.total_orders || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Orders
                  </Typography>
                  <Stack direction="row" alignItems="center" spacing={1} mt={1}>
                    {getGrowthIcon(metrics?.orders_growth || 0)}
                    <Typography 
                      variant="caption" 
                      color={getGrowthColor(metrics?.orders_growth || 0)}
                    >
                      {metrics?.orders_growth > 0 ? '+' : ''}{metrics?.orders_growth?.toFixed(1) || '0'}%
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
                  <CustomerIcon />
                </Avatar>
                <Box flex={1}>
                  <Typography variant="h4" component="div">
                    {metrics?.new_customers || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    New Customers
                  </Typography>
                  <Stack direction="row" alignItems="center" spacing={1} mt={1}>
                    {getGrowthIcon(metrics?.customer_growth || 0)}
                    <Typography 
                      variant="caption" 
                      color={getGrowthColor(metrics?.customer_growth || 0)}
                    >
                      {metrics?.customer_growth > 0 ? '+' : ''}{metrics?.customer_growth?.toFixed(1) || '0'}%
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
                <Avatar sx={{ bgcolor: 'warning.main', width: 56, height: 56 }}>
                  <DealIcon />
                </Avatar>
                <Box flex={1}>
                  <Typography variant="h4" component="div">
                    ${metrics?.avg_order_value?.toFixed(0) || '0'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Avg Order Value
                  </Typography>
                  <Typography variant="caption" color="text.secondary" mt={1}>
                    Conversion: {metrics?.conversion_rate?.toFixed(1) || '0'}%
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Order Status Overview */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={2}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <PendingIcon color="warning" sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h6">{metrics?.pending_orders || 0}</Typography>
              <Typography variant="caption" color="text.secondary">Pending</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={2}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <ShippingIcon color="info" sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h6">{metrics?.shipped_orders || 0}</Typography>
              <Typography variant="caption" color="text.secondary">Shipped</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={2}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <SuccessIcon color="success" sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h6">{metrics?.delivered_orders || 0}</Typography>
              <Typography variant="caption" color="text.secondary">Delivered</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={2}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <CancelledIcon color="error" sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h6">{metrics?.cancelled_orders || 0}</Typography>
              <Typography variant="caption" color="text.secondary">Cancelled</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader 
              title="Order Status Distribution" 
              titleTypographyProps={{ variant: 'h6' }}
            />
            <CardContent>
              {orderStatusData.length > 0 ? (
                <ResponsiveContainer width="100%" height={150}>
                  <PieChart>
                    <Pie
                      data={orderStatusData}
                      cx="50%"
                      cy="50%"
                      innerRadius={30}
                      outerRadius={60}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {orderStatusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <Alert severity="info">No order data available</Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts and Analytics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Sales Trend Chart */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardHeader 
              title="Sales Trends"
              action={
                <FormControl size="small" sx={{ minWidth: 100 }}>
                  <Select
                    value={selectedPeriod}
                    onChange={(e) => setSelectedPeriod(e.target.value)}
                  >
                    <MenuItem value="hourly">Hourly</MenuItem>
                    <MenuItem value="daily">Daily</MenuItem>
                    <MenuItem value="weekly">Weekly</MenuItem>
                    <MenuItem value="monthly">Monthly</MenuItem>
                  </Select>
                </FormControl>
              }
            />
            <CardContent>
              {metricsLoading ? (
                <LinearProgress />
              ) : salesTrends && salesTrends.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={salesTrends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis yAxisId="revenue" orientation="left" />
                    <YAxis yAxisId="orders" orientation="right" />
                    <Tooltip />
                    <Legend />
                    <Area
                      yAxisId="revenue"
                      type="monotone"
                      dataKey="revenue"
                      stackId="1"
                      stroke="#0088FE"
                      fill="#0088FE"
                      fillOpacity={0.6}
                      name="Revenue ($)"
                    />
                    <Line
                      yAxisId="orders"
                      type="monotone"
                      dataKey="orders"
                      stroke="#FF8042"
                      strokeWidth={2}
                      name="Orders"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <Alert severity="info">No trend data available for the selected period</Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Sales Targets */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardHeader title="Sales Targets" />
            <CardContent>
              <Stack spacing={3}>
                {salesTargets?.map((target, index) => (
                  <Box key={index}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
                      <Typography variant="subtitle2">{target.period}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {target.achievement_rate.toFixed(1)}%
                      </Typography>
                    </Stack>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min(target.achievement_rate, 100)}
                      color={target.achievement_rate >= 100 ? 'success' : target.achievement_rate >= 80 ? 'warning' : 'error'}
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                    <Stack direction="row" justifyContent="space-between" mt={1}>
                      <Typography variant="caption" color="text.secondary">
                        ${target.actual_revenue.toFixed(0)} / ${target.target_revenue.toFixed(0)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {target.actual_orders} / {target.target_orders} orders
                      </Typography>
                    </Stack>
                  </Box>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tables Section */}
      <Tabs value={currentTab} onChange={(_, newValue) => setCurrentTab(newValue)} sx={{ mb: 3 }}>
        <Tab icon={<TopIcon />} label="Top Products" />
        <Tab icon={<CustomerIcon />} label="Top Customers" />
        <Tab icon={<OrderIcon />} label="Recent Orders" />
      </Tabs>

      {/* Top Products Tab */}
      <TabPanel value={currentTab} index={0}>
        <Card>
          <CardHeader title="Top Selling Products" />
          <CardContent>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Product</TableCell>
                    <TableCell align="right">Qty Sold</TableCell>
                    <TableCell align="right">Revenue</TableCell>
                    <TableCell align="right">Profit Margin</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {topProducts?.map((product, index) => (
                    <TableRow key={product.product_id}>
                      <TableCell>
                        <Stack direction="row" alignItems="center" spacing={2}>
                          <Chip 
                            label={`#${index + 1}`} 
                            size="small" 
                            color={index < 3 ? 'primary' : 'default'}
                          />
                          <Box>
                            <Typography variant="body2" fontWeight="medium">
                              {product.product_name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {product.product_code}
                            </Typography>
                          </Box>
                        </Stack>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight="medium">
                          {product.quantity_sold}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight="medium" color="success.main">
                          ${product.revenue.toFixed(2)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography 
                          variant="body2" 
                          fontWeight="medium"
                          color={product.profit_margin > 20 ? 'success.main' : 'text.primary'}
                        >
                          {product.profit_margin.toFixed(1)}%
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </TabPanel>

      {/* Top Customers Tab */}
      <TabPanel value={currentTab} index={1}>
        <Card>
          <CardHeader title="Top Customers" />
          <CardContent>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Customer</TableCell>
                    <TableCell align="right">Orders</TableCell>
                    <TableCell align="right">Total Spent</TableCell>
                    <TableCell>Last Order</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {topCustomers?.map((customer, index) => (
                    <TableRow key={customer.customer_id}>
                      <TableCell>
                        <Stack direction="row" alignItems="center" spacing={2}>
                          <Chip 
                            label={`#${index + 1}`} 
                            size="small" 
                            color={index < 3 ? 'primary' : 'default'}
                          />
                          <Box>
                            <Typography variant="body2" fontWeight="medium">
                              {customer.customer_name}
                            </Typography>
                          </Box>
                        </Stack>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight="medium">
                          {customer.total_orders}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight="medium" color="success.main">
                          ${customer.total_spent.toFixed(2)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {new Date(customer.last_order_date).toLocaleDateString()}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </TabPanel>

      {/* Recent Orders Tab */}
      <TabPanel value={currentTab} index={2}>
        <Card>
          <CardHeader 
            title="Recent Orders"
            action={
              <Button
                variant="outlined"
                size="small"
                onClick={() => navigate('/sales/orders')}
              >
                View All
              </Button>
            }
          />
          <CardContent>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Order</TableCell>
                    <TableCell>Customer</TableCell>
                    <TableCell>Date</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Items</TableCell>
                    <TableCell align="right">Total</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {recentOrders?.map((order) => (
                    <TableRow key={order.id}>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace" fontWeight="medium">
                          {order.order_number}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {order.customer_name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {new Date(order.order_date).toLocaleDateString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={order.status}
                          size="small"
                          color={
                            order.status === 'delivered' ? 'success' :
                            order.status === 'shipped' ? 'info' :
                            order.status === 'cancelled' ? 'error' :
                            'warning'
                          }
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {order.items_count}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight="medium">
                          ${order.total_amount.toFixed(2)}
                        </Typography>
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

export default SalesDashboardPage;