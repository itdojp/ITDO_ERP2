import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Button,
  IconButton,
  Divider,
  Alert,
  LinearProgress,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Avatar,
  Tab,
  Tabs,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  ArrowBack as BackIcon,
  Inventory as InventoryIcon,
  AttachMoney as PriceIcon,
  LocalShipping as ShippingIcon,
  Info as InfoIcon,
  History as HistoryIcon,
  Assessment as AnalyticsIcon,
  Share as ShareIcon,
  Print as PrintIcon,
  ContentCopy as CopyIcon,
  QrCodeScanner as QrIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { apiClient } from '@/services/api';

interface Product {
  id: number;
  code: string;
  name: string;
  display_name: string;
  sku: string;
  standard_price: number;
  cost_price?: number;
  sale_price?: number;
  status: 'active' | 'inactive' | 'discontinued';
  product_type: 'product' | 'service' | 'kit';
  description?: string;
  category?: string;
  weight?: number;
  length?: number;
  width?: number;
  height?: number;
  barcode?: string;
  supplier?: string;
  lead_time_days?: number;
  minimum_stock_level?: number;
  reorder_point?: number;
  is_active: boolean;
  is_purchasable: boolean;
  is_sellable: boolean;
  is_trackable: boolean;
  tags?: string[];
  current_stock?: number;
  reserved_stock?: number;
  available_stock?: number;
  total_sales?: number;
  revenue?: number;
  created_at: string;
  updated_at: string;
}

interface StockMovement {
  id: number;
  type: 'in' | 'out' | 'adjustment';
  quantity: number;
  reference: string;
  date: string;
  notes?: string;
}

interface SalesRecord {
  id: number;
  order_id: string;
  quantity: number;
  unit_price: number;
  total: number;
  customer: string;
  date: string;
}

interface ProductAnalytics {
  total_sales: number;
  total_revenue: number;
  avg_monthly_sales: number;
  stock_turnover_rate: number;
  days_of_inventory: number;
  profit_margin: number;
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

export const ProductDetailPage: React.FC = () => {
  const { productId } = useParams<{ productId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  const [currentTab, setCurrentTab] = useState(0);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [stockAdjustmentOpen, setStockAdjustmentOpen] = useState(false);
  const [adjustmentQuantity, setAdjustmentQuantity] = useState('');
  const [adjustmentNotes, setAdjustmentNotes] = useState('');

  // Fetch product data
  const { data: product, isLoading, error, refetch } = useQuery({
    queryKey: ['product-detail', productId],
    queryFn: async (): Promise<Product> => {
      const response = await apiClient.get(`/api/v1/products-basic/${productId}`);
      return response.data;
    },
    enabled: !!productId,
  });

  // Fetch stock movements
  const { data: stockMovements } = useQuery({
    queryKey: ['stock-movements', productId],
    queryFn: async (): Promise<StockMovement[]> => {
      const response = await apiClient.get(`/api/v1/products-basic/${productId}/stock-movements`);
      return response.data || [];
    },
    enabled: !!productId,
  });

  // Fetch sales records
  const { data: salesRecords } = useQuery({
    queryKey: ['sales-records', productId],
    queryFn: async (): Promise<SalesRecord[]> => {
      const response = await apiClient.get(`/api/v1/products-basic/${productId}/sales`);
      return response.data || [];
    },
    enabled: !!productId,
  });

  // Fetch analytics
  const { data: analytics } = useQuery({
    queryKey: ['product-analytics', productId],
    queryFn: async (): Promise<ProductAnalytics> => {
      const response = await apiClient.get(`/api/v1/products-basic/${productId}/analytics`);
      return response.data || {
        total_sales: 0,
        total_revenue: 0,
        avg_monthly_sales: 0,
        stock_turnover_rate: 0,
        days_of_inventory: 0,
        profit_margin: 0,
      };
    },
    enabled: !!productId,
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async () => {
      await apiClient.delete(`/api/v1/products-basic/${productId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products-list'] });
      navigate('/products');
    },
  });

  // Stock adjustment mutation
  const stockAdjustmentMutation = useMutation({
    mutationFn: async (data: { quantity: number; notes: string }) => {
      await apiClient.post(`/api/v1/products-basic/${productId}/stock-adjustment`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['product-detail', productId] });
      queryClient.invalidateQueries({ queryKey: ['stock-movements', productId] });
      setStockAdjustmentOpen(false);
      setAdjustmentQuantity('');
      setAdjustmentNotes('');
    },
  });

  const handleDelete = async () => {
    await deleteMutation.mutateAsync();
    setDeleteDialogOpen(false);
  };

  const handleStockAdjustment = async () => {
    const quantity = parseFloat(adjustmentQuantity);
    if (!isNaN(quantity)) {
      await stockAdjustmentMutation.mutateAsync({
        quantity,
        notes: adjustmentNotes,
      });
    }
  };

  const handleCopyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  if (isLoading) {
    return (
      <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2 }}>Loading product details...</Typography>
      </Box>
    );
  }

  if (error || !product) {
    return (
      <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
        <Alert severity="error">
          Failed to load product details. Please try again.
          <Button onClick={() => refetch()} sx={{ ml: 2 }}>
            Retry
          </Button>
        </Alert>
      </Box>
    );
  }

  const stockStatus = product.current_stock === 0 ? 'out_of_stock' : 
    (product.current_stock || 0) <= (product.minimum_stock_level || 0) ? 'low_stock' : 'in_stock';

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
          <Stack direction="row" alignItems="center" spacing={2}>
            <IconButton onClick={() => navigate('/products')}>
              <BackIcon />
            </IconButton>
            <Box>
              <Typography variant="h4" component="h1">
                {product.display_name || product.name}
              </Typography>
              <Typography variant="body1" color="text.secondary">
                {product.code} • {product.sku}
              </Typography>
            </Box>
          </Stack>
          
          <Stack direction="row" spacing={2}>
            <IconButton onClick={() => refetch()}>
              <RefreshIcon />
            </IconButton>
            <IconButton onClick={() => handleCopyToClipboard(product.code)}>
              <CopyIcon />
            </IconButton>
            <IconButton>
              <QrIcon />
            </IconButton>
            <IconButton>
              <ShareIcon />
            </IconButton>
            <IconButton>
              <PrintIcon />
            </IconButton>
            <Button
              variant="outlined"
              startIcon={<EditIcon />}
              onClick={() => navigate(`/products/${productId}/edit`)}
            >
              Edit
            </Button>
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={() => setDeleteDialogOpen(true)}
            >
              Delete
            </Button>
          </Stack>
        </Stack>

        {/* Status Chips */}
        <Stack direction="row" spacing={1} flexWrap="wrap">
          <Chip
            label={product.status}
            color={product.status === 'active' ? 'success' : 'default'}
            variant={product.status === 'active' ? 'filled' : 'outlined'}
          />
          <Chip
            label={product.product_type}
            variant="outlined"
            color="primary"
          />
          <Chip
            label={stockStatus.replace('_', ' ')}
            color={stockStatus === 'in_stock' ? 'success' : stockStatus === 'low_stock' ? 'warning' : 'error'}
            variant="filled"
          />
          {product.is_active && <Chip label="Active" color="success" size="small" />}
          {product.is_purchasable && <Chip label="Purchasable" color="info" size="small" />}
          {product.is_sellable && <Chip label="Sellable" color="info" size="small" />}
          {product.is_trackable && <Chip label="Trackable" color="info" size="small" />}
        </Stack>
      </Paper>

      {/* Key Metrics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <PriceIcon />
                </Avatar>
                <Box>
                  <Typography variant="h5">${product.standard_price?.toFixed(2)}</Typography>
                  <Typography variant="body2" color="text.secondary">Standard Price</Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: 'success.main' }}>
                  <InventoryIcon />
                </Avatar>
                <Box>
                  <Typography variant="h5">{product.current_stock || 0}</Typography>
                  <Typography variant="body2" color="text.secondary">Current Stock</Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: 'info.main' }}>
                  <AnalyticsIcon />
                </Avatar>
                <Box>
                  <Typography variant="h5">{analytics?.total_sales || 0}</Typography>
                  <Typography variant="body2" color="text.secondary">Total Sales</Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: 'warning.main' }}>
                  <ShippingIcon />
                </Avatar>
                <Box>
                  <Typography variant="h5">${analytics?.total_revenue?.toFixed(2) || '0.00'}</Typography>
                  <Typography variant="body2" color="text.secondary">Total Revenue</Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tab Navigation */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={currentTab}
          onChange={(_, newValue) => setCurrentTab(newValue)}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<InfoIcon />} label="Details" />
          <Tab icon={<InventoryIcon />} label="Inventory" />
          <Tab icon={<HistoryIcon />} label="History" />
          <Tab icon={<AnalyticsIcon />} label="Analytics" />
        </Tabs>
      </Paper>

      {/* Product Details Tab */}
      <TabPanel value={currentTab} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12} lg={8}>
            <Card>
              <CardHeader title="Product Information" />
              <CardContent>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="text.secondary">Product Code</Typography>
                    <Typography variant="body1" fontFamily="monospace" fontWeight="medium">{product.code}</Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="text.secondary">SKU</Typography>
                    <Typography variant="body1" fontFamily="monospace">{product.sku}</Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="text.secondary">Name</Typography>
                    <Typography variant="body1">{product.name}</Typography>
                  </Grid>
                  {product.display_name !== product.name && (
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" color="text.secondary">Display Name</Typography>
                      <Typography variant="body1">{product.display_name}</Typography>
                    </Grid>
                  )}
                  {product.description && (
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" color="text.secondary">Description</Typography>
                      <Typography variant="body1">{product.description}</Typography>
                    </Grid>
                  )}
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="text.secondary">Category</Typography>
                    <Typography variant="body1">{product.category || '—'}</Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="text.secondary">Barcode</Typography>
                    <Typography variant="body1" fontFamily="monospace">{product.barcode || '—'}</Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>

            <Card sx={{ mt: 3 }}>
              <CardHeader title="Pricing Information" />
              <CardContent>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={4}>
                    <Typography variant="subtitle2" color="text.secondary">Standard Price</Typography>
                    <Typography variant="h6" color="primary">${product.standard_price?.toFixed(2)}</Typography>
                  </Grid>
                  {product.cost_price && (
                    <Grid item xs={12} md={4}>
                      <Typography variant="subtitle2" color="text.secondary">Cost Price</Typography>
                      <Typography variant="h6">${product.cost_price.toFixed(2)}</Typography>
                    </Grid>
                  )}
                  {product.sale_price && (
                    <Grid item xs={12} md={4}>
                      <Typography variant="subtitle2" color="text.secondary">Sale Price</Typography>
                      <Typography variant="h6" color="error">${product.sale_price.toFixed(2)}</Typography>
                    </Grid>
                  )}
                  {analytics && (
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" color="text.secondary">Profit Margin</Typography>
                      <Typography variant="h6" color={analytics.profit_margin > 0 ? 'success.main' : 'error.main'}>
                        {analytics.profit_margin.toFixed(1)}%
                      </Typography>
                    </Grid>
                  )}
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} lg={4}>
            <Card>
              <CardHeader title="Physical Properties" />
              <CardContent>
                <Grid container spacing={2}>
                  {product.weight && (
                    <Grid item xs={6}>
                      <Typography variant="subtitle2" color="text.secondary">Weight</Typography>
                      <Typography variant="body1">{product.weight} kg</Typography>
                    </Grid>
                  )}
                  {product.length && (
                    <Grid item xs={6}>
                      <Typography variant="subtitle2" color="text.secondary">Length</Typography>
                      <Typography variant="body1">{product.length} cm</Typography>
                    </Grid>
                  )}
                  {product.width && (
                    <Grid item xs={6}>
                      <Typography variant="subtitle2" color="text.secondary">Width</Typography>
                      <Typography variant="body1">{product.width} cm</Typography>
                    </Grid>
                  )}
                  {product.height && (
                    <Grid item xs={6}>
                      <Typography variant="subtitle2" color="text.secondary">Height</Typography>
                      <Typography variant="body1">{product.height} cm</Typography>
                    </Grid>
                  )}
                </Grid>
              </CardContent>
            </Card>

            <Card sx={{ mt: 3 }}>
              <CardHeader title="Supply Chain" />
              <CardContent>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="text.secondary">Supplier</Typography>
                    <Typography variant="body1">{product.supplier || '—'}</Typography>
                  </Grid>
                  {product.lead_time_days && (
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" color="text.secondary">Lead Time</Typography>
                      <Typography variant="body1">{product.lead_time_days} days</Typography>
                    </Grid>
                  )}
                </Grid>
              </CardContent>
            </Card>

            <Card sx={{ mt: 3 }}>
              <CardHeader title="Tags" />
              <CardContent>
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  {product.tags?.map((tag, index) => (
                    <Chip key={index} label={tag} size="small" variant="outlined" />
                  )) || <Typography color="text.secondary">No tags</Typography>}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Inventory Tab */}
      <TabPanel value={currentTab} index={1}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardHeader 
                title="Stock Information"
                action={
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setStockAdjustmentOpen(true)}
                  >
                    Adjust Stock
                  </Button>
                }
              />
              <CardContent>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={4}>
                    <Typography variant="subtitle2" color="text.secondary">Current Stock</Typography>
                    <Typography variant="h4">{product.current_stock || 0}</Typography>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Typography variant="subtitle2" color="text.secondary">Reserved</Typography>
                    <Typography variant="h4">{product.reserved_stock || 0}</Typography>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Typography variant="subtitle2" color="text.secondary">Available</Typography>
                    <Typography variant="h4">{product.available_stock || (product.current_stock || 0)}</Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="text.secondary">Minimum Level</Typography>
                    <Typography variant="body1">{product.minimum_stock_level || '—'}</Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="text.secondary">Reorder Point</Typography>
                    <Typography variant="body1">{product.reorder_point || '—'}</Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card>
              <CardHeader title="Stock Analytics" />
              <CardContent>
                {analytics && (
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" color="text.secondary">Turnover Rate</Typography>
                      <Typography variant="h6">{analytics.stock_turnover_rate.toFixed(2)}x</Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" color="text.secondary">Days of Inventory</Typography>
                      <Typography variant="h6">{Math.round(analytics.days_of_inventory)} days</Typography>
                    </Grid>
                  </Grid>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Recent Stock Movements */}
        <Card sx={{ mt: 3 }}>
          <CardHeader title="Recent Stock Movements" />
          <CardContent>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Date</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell align="right">Quantity</TableCell>
                    <TableCell>Reference</TableCell>
                    <TableCell>Notes</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {stockMovements?.slice(0, 10).map((movement) => (
                    <TableRow key={movement.id}>
                      <TableCell>{new Date(movement.date).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <Chip
                          label={movement.type}
                          size="small"
                          color={movement.type === 'in' ? 'success' : movement.type === 'out' ? 'error' : 'default'}
                        />
                      </TableCell>
                      <TableCell align="right">{movement.quantity}</TableCell>
                      <TableCell>{movement.reference}</TableCell>
                      <TableCell>{movement.notes || '—'}</TableCell>
                    </TableRow>
                  )) || (
                    <TableRow>
                      <TableCell colSpan={5} align="center">
                        <Typography color="text.secondary">No stock movements found</Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </TabPanel>

      {/* History Tab */}
      <TabPanel value={currentTab} index={2}>
        <Card>
          <CardHeader title="Sales History" />
          <CardContent>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Date</TableCell>
                    <TableCell>Order ID</TableCell>
                    <TableCell>Customer</TableCell>
                    <TableCell align="right">Quantity</TableCell>
                    <TableCell align="right">Unit Price</TableCell>
                    <TableCell align="right">Total</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {salesRecords?.map((sale) => (
                    <TableRow key={sale.id}>
                      <TableCell>{new Date(sale.date).toLocaleDateString()}</TableCell>
                      <TableCell>{sale.order_id}</TableCell>
                      <TableCell>{sale.customer}</TableCell>
                      <TableCell align="right">{sale.quantity}</TableCell>
                      <TableCell align="right">${sale.unit_price.toFixed(2)}</TableCell>
                      <TableCell align="right">${sale.total.toFixed(2)}</TableCell>
                    </TableRow>
                  )) || (
                    <TableRow>
                      <TableCell colSpan={6} align="center">
                        <Typography color="text.secondary">No sales records found</Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </TabPanel>

      {/* Analytics Tab */}
      <TabPanel value={currentTab} index={3}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Sales Performance" />
              <CardContent>
                {analytics && (
                  <Grid container spacing={3}>
                    <Grid item xs={6}>
                      <Typography variant="subtitle2" color="text.secondary">Total Sales</Typography>
                      <Typography variant="h5">{analytics.total_sales}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="subtitle2" color="text.secondary">Total Revenue</Typography>
                      <Typography variant="h5">${analytics.total_revenue.toFixed(2)}</Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" color="text.secondary">Average Monthly Sales</Typography>
                      <Typography variant="h6">{analytics.avg_monthly_sales.toFixed(1)} units</Typography>
                    </Grid>
                  </Grid>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Inventory Metrics" />
              <CardContent>
                {analytics && (
                  <Grid container spacing={3}>
                    <Grid item xs={6}>
                      <Typography variant="subtitle2" color="text.secondary">Stock Turnover</Typography>
                      <Typography variant="h5">{analytics.stock_turnover_rate.toFixed(2)}x</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="subtitle2" color="text.secondary">Days of Inventory</Typography>
                      <Typography variant="h5">{Math.round(analytics.days_of_inventory)}</Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" color="text.secondary">Profit Margin</Typography>
                      <Typography variant="h6" color={analytics.profit_margin > 0 ? 'success.main' : 'error.main'}>
                        {analytics.profit_margin.toFixed(1)}%
                      </Typography>
                    </Grid>
                  </Grid>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12}>
            <Card>
              <CardHeader title="Audit Trail" />
              <CardContent>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="text.secondary">Created</Typography>
                    <Typography variant="body1">{new Date(product.created_at).toLocaleString()}</Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="text.secondary">Last Updated</Typography>
                    <Typography variant="body1">{new Date(product.updated_at).toLocaleString()}</Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Product</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{product.name}"? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleDelete}
            color="error"
            variant="contained"
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Stock Adjustment Dialog */}
      <Dialog open={stockAdjustmentOpen} onClose={() => setStockAdjustmentOpen(false)}>
        <DialogTitle>Adjust Stock</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Current stock: {product.current_stock || 0} units
          </Typography>
          <TextField
            autoFocus
            margin="dense"
            label="Adjustment Quantity"
            type="number"
            fullWidth
            variant="outlined"
            value={adjustmentQuantity}
            onChange={(e) => setAdjustmentQuantity(e.target.value)}
            helperText="Use positive numbers to add stock, negative to reduce"
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Notes (optional)"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={adjustmentNotes}
            onChange={(e) => setAdjustmentNotes(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStockAdjustmentOpen(false)}>Cancel</Button>
          <Button
            onClick={handleStockAdjustment}
            variant="contained"
            disabled={stockAdjustmentMutation.isPending || !adjustmentQuantity}
          >
            {stockAdjustmentMutation.isPending ? 'Adjusting...' : 'Adjust Stock'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ProductDetailPage;