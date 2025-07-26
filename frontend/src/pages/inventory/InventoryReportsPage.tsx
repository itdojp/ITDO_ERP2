import React, { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  DatePicker,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  Avatar,
  Divider,
  Alert,
} from "@mui/material";
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
  Inventory as InventoryIcon,
  AttachMoney as MoneyIcon,
  Speed as VelocityIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Category as CategoryIcon,
  Business as SupplierIcon,
} from "@mui/icons-material";
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
  ResponsiveContainer,
} from "recharts";
import { apiClient } from "@/services/api";

interface InventoryAnalytics {
  total_items: number;
  total_value: number;
  avg_turnover_rate: number;
  low_stock_items: number;
  out_of_stock_items: number;
  overstock_items: number;
  dead_stock_items: number;
  carrying_cost: number;
  stockout_cost: number;
  accuracy_rate: number;
}

interface TurnoverAnalysis {
  product_id: number;
  product_code: string;
  product_name: string;
  category: string;
  current_stock: number;
  avg_monthly_sales: number;
  turnover_rate: number;
  days_of_inventory: number;
  classification: "fast" | "medium" | "slow" | "dead";
  last_sale_date?: string;
}

interface StockValueAnalysis {
  category: string;
  total_value: number;
  percentage: number;
  item_count: number;
  avg_value_per_item: number;
}

interface MovementTrend {
  date: string;
  receipts: number;
  shipments: number;
  adjustments: number;
  net_movement: number;
}

interface ABCAnalysis {
  product_id: number;
  product_code: string;
  product_name: string;
  annual_usage_value: number;
  percentage_of_total: number;
  cumulative_percentage: number;
  abc_class: "A" | "B" | "C";
}

interface ReorderReport {
  product_id: number;
  product_code: string;
  product_name: string;
  current_stock: number;
  reorder_point: number;
  recommended_order_qty: number;
  supplier: string;
  lead_time_days: number;
  priority: "urgent" | "normal" | "low";
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

const COLORS = [
  "#0088FE",
  "#00C49F",
  "#FFBB28",
  "#FF8042",
  "#8884D8",
  "#82CA9D",
];

export const InventoryReportsPage: React.FC = () => {
  const navigate = useNavigate();

  const [currentTab, setCurrentTab] = useState(0);
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
      .toISOString()
      .split("T")[0],
    end: new Date().toISOString().split("T")[0],
  });
  const [selectedWarehouse, setSelectedWarehouse] = useState("all");
  const [selectedCategory, setSelectedCategory] = useState("all");

  // Fetch inventory analytics
  const { data: analytics, isLoading: analyticsLoading } = useQuery({
    queryKey: [
      "inventory-analytics",
      dateRange,
      selectedWarehouse,
      selectedCategory,
    ],
    queryFn: async (): Promise<InventoryAnalytics> => {
      const params = new URLSearchParams({
        start_date: dateRange.start,
        end_date: dateRange.end,
        warehouse: selectedWarehouse,
        category: selectedCategory,
      });
      const response = await apiClient.get(
        `/api/v1/inventory/analytics?${params}`,
      );
      return (
        response.data || {
          total_items: 0,
          total_value: 0,
          avg_turnover_rate: 0,
          low_stock_items: 0,
          out_of_stock_items: 0,
          overstock_items: 0,
          dead_stock_items: 0,
          carrying_cost: 0,
          stockout_cost: 0,
          accuracy_rate: 0,
        }
      );
    },
  });

  // Fetch turnover analysis
  const { data: turnoverData } = useQuery({
    queryKey: ["inventory-turnover", dateRange],
    queryFn: async (): Promise<TurnoverAnalysis[]> => {
      const params = new URLSearchParams({
        start_date: dateRange.start,
        end_date: dateRange.end,
      });
      const response = await apiClient.get(
        `/api/v1/inventory/turnover-analysis?${params}`,
      );
      return response.data || [];
    },
  });

  // Fetch stock value analysis
  const { data: stockValueData } = useQuery({
    queryKey: ["inventory-value-analysis"],
    queryFn: async (): Promise<StockValueAnalysis[]> => {
      const response = await apiClient.get("/api/v1/inventory/value-analysis");
      return response.data || [];
    },
  });

  // Fetch movement trends
  const { data: movementTrends } = useQuery({
    queryKey: ["inventory-movement-trends", dateRange],
    queryFn: async (): Promise<MovementTrend[]> => {
      const params = new URLSearchParams({
        start_date: dateRange.start,
        end_date: dateRange.end,
      });
      const response = await apiClient.get(
        `/api/v1/inventory/movement-trends?${params}`,
      );
      return response.data || [];
    },
  });

  // Fetch ABC analysis
  const { data: abcAnalysis } = useQuery({
    queryKey: ["inventory-abc-analysis"],
    queryFn: async (): Promise<ABCAnalysis[]> => {
      const response = await apiClient.get("/api/v1/inventory/abc-analysis");
      return response.data || [];
    },
  });

  // Fetch reorder report
  const { data: reorderReport } = useQuery({
    queryKey: ["inventory-reorder-report"],
    queryFn: async (): Promise<ReorderReport[]> => {
      const response = await apiClient.get("/api/v1/inventory/reorder-report");
      return response.data || [];
    },
  });

  // Process data for charts
  const turnoverChartData = useMemo(() => {
    if (!turnoverData) return [];

    const grouped = turnoverData.reduce((acc, item) => {
      const key = item.classification;
      if (!acc[key]) {
        acc[key] = { classification: key, count: 0, total_value: 0 };
      }
      acc[key].count += 1;
      acc[key].total_value +=
        item.current_stock * (item.avg_monthly_sales || 0);
      return acc;
    }, {} as any);

    return Object.values(grouped);
  }, [turnoverData]);

  const exportReport = (type: "pdf" | "excel" | "csv") => {
    const params = new URLSearchParams({
      type,
      start_date: dateRange.start,
      end_date: dateRange.end,
      warehouse: selectedWarehouse,
      category: selectedCategory,
    });
    window.open(`/api/v1/inventory/export-report?${params}`, "_blank");
  };

  const scheduleReport = () => {
    // Schedule report functionality
    console.log("Schedule report");
  };

  return (
    <Box sx={{ maxWidth: 1400, mx: "auto", p: 3 }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          mb={3}
        >
          <Typography variant="h4" component="h1">
            Inventory Reports & Analytics
          </Typography>

          <Stack direction="row" spacing={2}>
            <Button
              variant="outlined"
              startIcon={<ScheduleIcon />}
              onClick={scheduleReport}
            >
              Schedule
            </Button>
            <Button variant="outlined" startIcon={<EmailIcon />}>
              Email
            </Button>
            <Button variant="outlined" startIcon={<PrintIcon />}>
              Print
            </Button>
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={() => exportReport("pdf")}
            >
              Export
            </Button>
          </Stack>
        </Stack>

        {/* Filters */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={3}>
            <TextField
              label="Start Date"
              type="date"
              fullWidth
              value={dateRange.start}
              onChange={(e) =>
                setDateRange((prev) => ({ ...prev, start: e.target.value }))
              }
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <TextField
              label="End Date"
              type="date"
              fullWidth
              value={dateRange.end}
              onChange={(e) =>
                setDateRange((prev) => ({ ...prev, end: e.target.value }))
              }
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Warehouse</InputLabel>
              <Select
                value={selectedWarehouse}
                onChange={(e) => setSelectedWarehouse(e.target.value)}
                label="Warehouse"
              >
                <MenuItem value="all">All Warehouses</MenuItem>
                <MenuItem value="main">Main Warehouse</MenuItem>
                <MenuItem value="secondary">Secondary Warehouse</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Category</InputLabel>
              <Select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                label="Category"
              >
                <MenuItem value="all">All Categories</MenuItem>
                <MenuItem value="electronics">Electronics</MenuItem>
                <MenuItem value="clothing">Clothing</MenuItem>
                <MenuItem value="books">Books</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Key Metrics Dashboard */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: "primary.main" }}>
                  <InventoryIcon />
                </Avatar>
                <Box>
                  <Typography variant="h4">
                    {analytics?.total_items || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Items
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: "success.main" }}>
                  <MoneyIcon />
                </Avatar>
                <Box>
                  <Typography variant="h4">
                    ${analytics?.total_value?.toFixed(0) || "0"}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Value
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: "info.main" }}>
                  <VelocityIcon />
                </Avatar>
                <Box>
                  <Typography variant="h4">
                    {analytics?.avg_turnover_rate?.toFixed(1) || "0.0"}x
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Avg Turnover
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: "warning.main" }}>
                  <WarningIcon />
                </Avatar>
                <Box>
                  <Typography variant="h4">
                    {analytics?.low_stock_items || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Low Stock
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Secondary Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={2}>
          <Card>
            <CardContent sx={{ textAlign: "center" }}>
              <ErrorIcon color="error" sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h6">
                {analytics?.out_of_stock_items || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Out of Stock
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={2}>
          <Card>
            <CardContent sx={{ textAlign: "center" }}>
              <TrendingUpIcon color="info" sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h6">
                {analytics?.overstock_items || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Overstock
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={2}>
          <Card>
            <CardContent sx={{ textAlign: "center" }}>
              <TrendingDownIcon
                color="secondary"
                sx={{ fontSize: 32, mb: 1 }}
              />
              <Typography variant="h6">
                {analytics?.dead_stock_items || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Dead Stock
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={2}>
          <Card>
            <CardContent sx={{ textAlign: "center" }}>
              <MoneyIcon color="warning" sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h6">
                ${analytics?.carrying_cost?.toFixed(0) || "0"}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Carrying Cost
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={2}>
          <Card>
            <CardContent sx={{ textAlign: "center" }}>
              <ErrorIcon color="error" sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h6">
                ${analytics?.stockout_cost?.toFixed(0) || "0"}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Stockout Cost
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={2}>
          <Card>
            <CardContent sx={{ textAlign: "center" }}>
              <CheckIcon color="success" sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h6">
                {analytics?.accuracy_rate?.toFixed(1) || "0.0"}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Accuracy
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={currentTab}
          onChange={(_, newValue) => setCurrentTab(newValue)}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<LineChartIcon />} label="Movement Trends" />
          <Tab icon={<PieChartIcon />} label="Stock Value Analysis" />
          <Tab icon={<BarChartIcon />} label="Turnover Analysis" />
          <Tab icon={<CategoryIcon />} label="ABC Analysis" />
          <Tab icon={<WarningIcon />} label="Reorder Report" />
        </Tabs>
      </Paper>

      {/* Movement Trends Tab */}
      <TabPanel value={currentTab} index={0}>
        <Card>
          <CardHeader title="Inventory Movement Trends" />
          <CardContent>
            {movementTrends && movementTrends.length > 0 ? (
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={movementTrends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="receipts"
                    stroke="#00C49F"
                    name="Receipts"
                  />
                  <Line
                    type="monotone"
                    dataKey="shipments"
                    stroke="#FF8042"
                    name="Shipments"
                  />
                  <Line
                    type="monotone"
                    dataKey="adjustments"
                    stroke="#8884D8"
                    name="Adjustments"
                  />
                  <Line
                    type="monotone"
                    dataKey="net_movement"
                    stroke="#0088FE"
                    name="Net Movement"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <Alert severity="info">
                No movement data available for the selected period.
              </Alert>
            )}
          </CardContent>
        </Card>
      </TabPanel>

      {/* Stock Value Analysis Tab */}
      <TabPanel value={currentTab} index={1}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Value Distribution by Category" />
              <CardContent>
                {stockValueData && stockValueData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={stockValueData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={(entry) =>
                          `${entry.category}: ${entry.percentage.toFixed(1)}%`
                        }
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="total_value"
                      >
                        {stockValueData.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={COLORS[index % COLORS.length]}
                          />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(value: number) => [
                          `$${value.toFixed(0)}`,
                          "Value",
                        ]}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <Alert severity="info">No stock value data available.</Alert>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Category Breakdown" />
              <CardContent>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Category</TableCell>
                        <TableCell align="right">Items</TableCell>
                        <TableCell align="right">Value</TableCell>
                        <TableCell align="right">Percentage</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {stockValueData?.map((row) => (
                        <TableRow key={row.category}>
                          <TableCell>{row.category}</TableCell>
                          <TableCell align="right">{row.item_count}</TableCell>
                          <TableCell align="right">
                            ${row.total_value.toFixed(0)}
                          </TableCell>
                          <TableCell align="right">
                            {row.percentage.toFixed(1)}%
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

      {/* Turnover Analysis Tab */}
      <TabPanel value={currentTab} index={2}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Turnover Rate Distribution" />
              <CardContent>
                {turnoverChartData && turnoverChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={turnoverChartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="classification" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="count" fill="#0088FE" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <Alert severity="info">No turnover data available.</Alert>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Slow Moving Items" />
              <CardContent>
                <TableContainer sx={{ maxHeight: 300 }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell>Product</TableCell>
                        <TableCell align="right">Stock</TableCell>
                        <TableCell align="right">Turnover</TableCell>
                        <TableCell align="right">DOI</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {turnoverData
                        ?.filter(
                          (item) =>
                            item.classification === "slow" ||
                            item.classification === "dead",
                        )
                        .slice(0, 10)
                        .map((item) => (
                          <TableRow key={item.product_id}>
                            <TableCell>
                              <Box>
                                <Typography variant="body2" fontWeight="medium">
                                  {item.product_name}
                                </Typography>
                                <Typography
                                  variant="caption"
                                  color="text.secondary"
                                >
                                  {item.product_code}
                                </Typography>
                              </Box>
                            </TableCell>
                            <TableCell align="right">
                              {item.current_stock}
                            </TableCell>
                            <TableCell align="right">
                              {item.turnover_rate.toFixed(2)}x
                            </TableCell>
                            <TableCell align="right">
                              {Math.round(item.days_of_inventory)}d
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

      {/* ABC Analysis Tab */}
      <TabPanel value={currentTab} index={3}>
        <Card>
          <CardHeader title="ABC Analysis - Pareto Classification" />
          <CardContent>
            {analyticsLoading ? (
              <LinearProgress />
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Product</TableCell>
                      <TableCell>Class</TableCell>
                      <TableCell align="right">Annual Usage Value</TableCell>
                      <TableCell align="right">% of Total</TableCell>
                      <TableCell align="right">Cumulative %</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {abcAnalysis?.slice(0, 20).map((item) => (
                      <TableRow key={item.product_id}>
                        <TableCell>
                          <Box>
                            <Typography variant="body2" fontWeight="medium">
                              {item.product_name}
                            </Typography>
                            <Typography
                              variant="caption"
                              color="text.secondary"
                            >
                              {item.product_code}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={`Class ${item.abc_class}`}
                            size="small"
                            color={
                              item.abc_class === "A"
                                ? "error"
                                : item.abc_class === "B"
                                  ? "warning"
                                  : "info"
                            }
                          />
                        </TableCell>
                        <TableCell align="right">
                          ${item.annual_usage_value.toFixed(0)}
                        </TableCell>
                        <TableCell align="right">
                          {item.percentage_of_total.toFixed(1)}%
                        </TableCell>
                        <TableCell align="right">
                          {item.cumulative_percentage.toFixed(1)}%
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      </TabPanel>

      {/* Reorder Report Tab */}
      <TabPanel value={currentTab} index={4}>
        <Card>
          <CardHeader
            title="Reorder Report"
            subheader="Items that need to be reordered based on current stock levels"
          />
          <CardContent>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Product</TableCell>
                    <TableCell align="right">Current Stock</TableCell>
                    <TableCell align="right">Reorder Point</TableCell>
                    <TableCell align="right">Recommended Qty</TableCell>
                    <TableCell>Supplier</TableCell>
                    <TableCell align="right">Lead Time</TableCell>
                    <TableCell>Priority</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {reorderReport?.map((item) => (
                    <TableRow key={item.product_id}>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {item.product_name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {item.product_code}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <Typography
                          variant="body2"
                          color={
                            item.current_stock <= item.reorder_point
                              ? "error.main"
                              : "text.primary"
                          }
                        >
                          {item.current_stock}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">{item.reorder_point}</TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight="medium">
                          {item.recommended_order_qty}
                        </Typography>
                      </TableCell>
                      <TableCell>{item.supplier}</TableCell>
                      <TableCell align="right">
                        {item.lead_time_days} days
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={item.priority}
                          size="small"
                          color={
                            item.priority === "urgent"
                              ? "error"
                              : item.priority === "normal"
                                ? "warning"
                                : "info"
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

export default InventoryReportsPage;
