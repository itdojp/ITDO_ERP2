import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataGrid, GridColDef, GridRowSelectionModel, GridToolbar, GridActionsCellItem, GridRenderCellParams } from '@mui/x-data-grid';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  IconButton,
  Stack,
  Card,
  CardContent,
  Chip,
  Avatar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Drawer,
  Grid,
  Divider,
  Badge,
  Tooltip
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Inventory as InventoryIcon,
  AttachMoney as PriceIcon,
  Warning as WarningIcon,
  CheckCircle as ActiveIcon,
  Visibility as ViewIcon,
  Refresh as RefreshIcon,
  Download as ExportIcon,
  Upload as ImportIcon,
  ShoppingCart as CartIcon,
  TrendingUp as TrendingUpIcon,
  Category as CategoryIcon
} from '@mui/icons-material';
import { apiClient } from '@/services/api';

interface Product {
  id: number;
  code: string;
  name: string;
  sku: string;
  price: number;
  cost_price?: number;
  stock: number;
  category: string;
  status: 'active' | 'inactive' | 'discontinued';
  is_active: boolean;
  supplier?: string;
  last_updated: string;
  total_sales?: number;
  profit_margin?: number;
  stock_status: 'in_stock' | 'low_stock' | 'out_of_stock';
}

interface ProductFilters {
  search: string;
  category: string;
  status: string;
  stock_status: string;
  supplier: string;
  price_min: string;
  price_max: string;
}

export const ProductListPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  // States
  const [selectedRows, setSelectedRows] = useState<GridRowSelectionModel>([]);
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  
  const [paginationModel, setPaginationModel] = useState({
    page: 0,
    pageSize: 25,
  });
  
  const [filters, setFilters] = useState<ProductFilters>({
    search: '',
    category: '',
    status: '',
    stock_status: '',
    supplier: '',
    price_min: '',
    price_max: ''
  });

  // Mock data for initial development - replace with real API
  const mockProducts: Product[] = [
    {
      id: 1,
      code: 'PROD001',
      name: 'Ultra Gaming Laptop X1',
      sku: 'LAP-X1-001',
      price: 1299.99,
      cost_price: 950.00,
      stock: 45,
      category: 'Electronics',
      status: 'active',
      is_active: true,
      supplier: 'TechCorp Ltd',
      last_updated: '2024-01-15T10:30:00Z',
      total_sales: 156,
      profit_margin: 26.9,
      stock_status: 'in_stock'
    },
    {
      id: 2,
      code: 'PROD002', 
      name: 'Wireless Bluetooth Headphones Pro',
      sku: 'HEAD-PRO-002',
      price: 199.99,
      cost_price: 125.00,
      stock: 8,
      category: 'Audio',
      status: 'active',
      is_active: true,
      supplier: 'AudioMax Inc',
      last_updated: '2024-01-14T15:45:00Z',
      total_sales: 89,
      profit_margin: 37.5,
      stock_status: 'low_stock'
    },
    {
      id: 3,
      code: 'PROD003',
      name: 'Smart Home Security Camera 4K',
      sku: 'CAM-4K-003',
      price: 299.99,
      cost_price: 180.00,
      stock: 0,
      category: 'Security',
      status: 'active',
      is_active: true,
      supplier: 'SecureTech Solutions',
      last_updated: '2024-01-13T09:20:00Z',
      total_sales: 67,
      profit_margin: 40.0,
      stock_status: 'out_of_stock'
    },
    {
      id: 4,
      code: 'PROD004',
      name: 'Professional Drone with 4K Camera',
      sku: 'DRONE-4K-004',
      price: 899.99,
      cost_price: 650.00,
      stock: 23,
      category: 'Drones',
      status: 'active',
      is_active: true,
      supplier: 'SkyTech Manufacturing',
      last_updated: '2024-01-12T14:10:00Z',
      total_sales: 34,
      profit_margin: 27.8,
      stock_status: 'in_stock'
    },
    {
      id: 5,
      code: 'PROD005',
      name: 'Vintage Mechanical Keyboard RGB',
      sku: 'KEY-RGB-005',
      price: 159.99,
      cost_price: 89.00,
      stock: 67,
      category: 'Peripherals',
      status: 'active',
      is_active: true,
      supplier: 'KeyCraft Ltd',
      last_updated: '2024-01-11T11:30:00Z',
      total_sales: 234,
      profit_margin: 44.4,
      stock_status: 'in_stock'
    }
  ];

  // Real-time data fetching (mocked for now)
  const { data: productData, isLoading, error, refetch } = useQuery({
    queryKey: ['products-list', filters, paginationModel],
    queryFn: async () => {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Filter mock data based on current filters
      let filteredProducts = mockProducts;
      
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        filteredProducts = filteredProducts.filter(p => 
          p.name.toLowerCase().includes(searchLower) ||
          p.code.toLowerCase().includes(searchLower) ||
          p.sku.toLowerCase().includes(searchLower)
        );
      }
      
      if (filters.category) {
        filteredProducts = filteredProducts.filter(p => p.category === filters.category);
      }
      
      if (filters.status) {
        filteredProducts = filteredProducts.filter(p => p.status === filters.status);
      }
      
      if (filters.stock_status) {
        filteredProducts = filteredProducts.filter(p => p.stock_status === filters.stock_status);
      }
      
      return {
        products: filteredProducts,
        total: filteredProducts.length,
        summary: {
          total_products: mockProducts.length,
          active_products: mockProducts.filter(p => p.is_active).length,
          low_stock_count: mockProducts.filter(p => p.stock_status === 'low_stock').length,
          out_of_stock_count: mockProducts.filter(p => p.stock_status === 'out_of_stock').length,
          total_value: mockProducts.reduce((sum, p) => sum + (p.price * p.stock), 0)
        }
      };
    },
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  });

  // Delete mutation (mocked)
  const deleteMutation = useMutation({
    mutationFn: async (productIds: number[]) => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      console.log('Deleting products:', productIds);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products-list'] });
      setSelectedRows([]);
      setDeleteDialogOpen(false);
    },
  });

  // DataGrid columns with advanced features
  const columns: GridColDef[] = useMemo(() => [
    {
      field: 'code',
      headerName: 'Code',
      width: 130,
      renderCell: (params: GridRenderCellParams) => (
        <Typography variant="body2" fontFamily="monospace" fontWeight="medium" color="primary">
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'name',
      headerName: 'Product Name', 
      width: 280,
      renderCell: (params: GridRenderCellParams) => (
        <Box>
          <Typography variant="body2" fontWeight="medium" noWrap>
            {params.value}
          </Typography>
          <Typography variant="caption" color="text.secondary" noWrap>
            SKU: {params.row.sku}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'category',
      headerName: 'Category',
      width: 120,
      renderCell: (params: GridRenderCellParams) => (
        <Chip
          label={params.value}
          size="small"
          variant="outlined"
          color="primary"
          icon={<CategoryIcon />}
        />
      ),
    },
    {
      field: 'price',
      headerName: 'Price',
      width: 120,
      type: 'number',
      renderCell: (params: GridRenderCellParams) => (
        <Box textAlign="right">
          <Typography variant="body2" fontWeight="bold" color="success.main">
            ${params.value.toFixed(2)}
          </Typography>
          {params.row.profit_margin && (
            <Typography variant="caption" color="text.secondary">
              {params.row.profit_margin.toFixed(1)}% margin
            </Typography>
          )}
        </Box>
      ),
    },
    {
      field: 'stock',
      headerName: 'Stock',
      width: 100,
      type: 'number',
      renderCell: (params: GridRenderCellParams) => {
        const stockStatus = params.row.stock_status;
        const stockValue = params.value as number;
        
        return (
          <Box textAlign="center">
            <Typography
              variant="body2"
              fontWeight="bold"
              color={
                stockStatus === 'out_of_stock' ? 'error.main' :
                stockStatus === 'low_stock' ? 'warning.main' :
                'success.main'
              }
            >
              {stockValue}
            </Typography>
            <Chip
              label={stockStatus.replace('_', ' ')}
              size="small"
              color={
                stockStatus === 'out_of_stock' ? 'error' :
                stockStatus === 'low_stock' ? 'warning' :
                'success'
              }
              variant="filled"
            />
          </Box>
        );
      },
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params: GridRenderCellParams) => (
        <Chip
          label={params.value}
          size="small"
          color={params.value === 'active' ? 'success' : 'default'}
          variant={params.value === 'active' ? 'filled' : 'outlined'}
          icon={params.value === 'active' ? <ActiveIcon /> : <WarningIcon />}
        />
      ),
    },
    {
      field: 'supplier',
      headerName: 'Supplier',
      width: 150,
      renderCell: (params: GridRenderCellParams) => (
        <Typography variant="body2" noWrap>
          {params.value || '—'}
        </Typography>
      ),
    },
    {
      field: 'total_sales',
      headerName: 'Sales',
      width: 100,
      type: 'number',
      renderCell: (params: GridRenderCellParams) => (
        <Box textAlign="center">
          <Typography variant="body2" fontWeight="medium">
            {params.value || 0}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            units
          </Typography>
        </Box>
      ),
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 150,
      getActions: (params) => [
        <GridActionsCellItem
          icon={<ViewIcon />}
          label="View"
          onClick={() => navigate(`/products/${params.id}`)}
          showInMenu
        />,
        <GridActionsCellItem
          icon={<EditIcon />}
          label="Edit"
          onClick={() => navigate(`/products/${params.id}/edit`)}
          showInMenu
        />,
        <GridActionsCellItem
          icon={<CartIcon />}
          label="Add to Order"
          onClick={() => handleAddToOrder(params.row)}
          showInMenu
        />,
        <GridActionsCellItem
          icon={<DeleteIcon />}
          label="Delete"
          onClick={() => handleDeleteSingle(params.row)}
          color="error"
          showInMenu
        />,
      ],
    },
  ], [navigate]);

  // Event handlers
  const handleFilterChange = (field: keyof ProductFilters, value: string) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    setPaginationModel(prev => ({ ...prev, page: 0 }));
  };

  const handleClearFilters = () => {
    setFilters({
      search: '',
      category: '',
      status: '',
      stock_status: '',
      supplier: '',
      price_min: '',
      price_max: ''
    });
  };

  const handleDeleteSingle = (product: Product) => {
    setSelectedProduct(product);
    setDeleteDialogOpen(true);
  };

  const handleBulkDelete = () => {
    if (selectedRows.length > 0) {
      setDeleteDialogOpen(true);
    }
  };

  const confirmDelete = async () => {
    if (selectedProduct) {
      await deleteMutation.mutateAsync([selectedProduct.id]);
    } else if (selectedRows.length > 0) {
      await deleteMutation.mutateAsync(selectedRows as number[]);
    }
  };

  const handleAddToOrder = (product: Product) => {
    console.log('Adding to order:', product);
    // Navigate to order creation with pre-filled product
    navigate('/orders/new', { state: { preFilledProduct: product } });
  };

  const handleExport = () => {
    console.log('Exporting products with filters:', filters);
    // Implement export functionality
  };

  // Filter drawer component
  const FilterDrawer = () => (
    <Drawer
      anchor="right"
      open={filterDrawerOpen}
      onClose={() => setFilterDrawerOpen(false)}
      PaperProps={{ sx: { width: 400, p: 3 } }}
    >
      <Typography variant="h6" gutterBottom>
        Filter Products
      </Typography>
      
      <Stack spacing={3}>
        <TextField
          label="Search"
          placeholder="Search by name, code, or SKU..."
          value={filters.search}
          onChange={(e) => handleFilterChange('search', e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
          }}
          fullWidth
        />

        <FormControl fullWidth>
          <InputLabel>Category</InputLabel>
          <Select
            value={filters.category}
            onChange={(e) => handleFilterChange('category', e.target.value)}
            label="Category"
          >
            <MenuItem value="">All Categories</MenuItem>
            <MenuItem value="Electronics">Electronics</MenuItem>
            <MenuItem value="Audio">Audio</MenuItem>
            <MenuItem value="Security">Security</MenuItem>
            <MenuItem value="Drones">Drones</MenuItem>
            <MenuItem value="Peripherals">Peripherals</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>Status</InputLabel>
          <Select
            value={filters.status}
            onChange={(e) => handleFilterChange('status', e.target.value)}
            label="Status"
          >
            <MenuItem value="">All Status</MenuItem>
            <MenuItem value="active">Active</MenuItem>
            <MenuItem value="inactive">Inactive</MenuItem>
            <MenuItem value="discontinued">Discontinued</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>Stock Status</InputLabel>
          <Select
            value={filters.stock_status}
            onChange={(e) => handleFilterChange('stock_status', e.target.value)}
            label="Stock Status"
          >
            <MenuItem value="">All Stock Levels</MenuItem>
            <MenuItem value="in_stock">In Stock</MenuItem>
            <MenuItem value="low_stock">Low Stock</MenuItem>
            <MenuItem value="out_of_stock">Out of Stock</MenuItem>
          </Select>
        </FormControl>

        <TextField
          label="Supplier"
          value={filters.supplier}
          onChange={(e) => handleFilterChange('supplier', e.target.value)}
          fullWidth
        />

        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Price Range
          </Typography>
          <Stack direction="row" spacing={2}>
            <TextField
              label="Min Price"
              type="number"
              value={filters.price_min}
              onChange={(e) => handleFilterChange('price_min', e.target.value)}
              size="small"
              InputProps={{ startAdornment: '$' }}
            />
            <TextField
              label="Max Price"
              type="number"
              value={filters.price_max}
              onChange={(e) => handleFilterChange('price_max', e.target.value)}
              size="small"
              InputProps={{ startAdornment: '$' }}
            />
          </Stack>
        </Box>

        <Divider />

        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            onClick={handleClearFilters}
            fullWidth
          >
            Clear All
          </Button>
          <Button
            variant="contained"
            onClick={() => setFilterDrawerOpen(false)}
            fullWidth
          >
            Apply Filters
          </Button>
        </Stack>
      </Stack>
    </Drawer>
  );

  const activeFiltersCount = Object.values(filters).filter(value => value !== '').length;

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">
          Failed to load products. Please try again.
          <Button onClick={() => refetch()} sx={{ ml: 2 }}>
            Retry
          </Button>
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 2 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar sx={{ bgcolor: 'primary.main' }}>
              <InventoryIcon />
            </Avatar>
            Product Management
          </Typography>
          
          <Stack direction="row" spacing={2}>
            <Tooltip title="Refresh data">
              <IconButton onClick={() => refetch()} disabled={isLoading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            
            <Badge badgeContent={activeFiltersCount} color="primary">
              <Button
                variant="outlined"
                startIcon={<FilterIcon />}
                onClick={() => setFilterDrawerOpen(true)}
              >
                Filters
              </Button>
            </Badge>
            
            <Button
              variant="outlined"
              startIcon={<ExportIcon />}
              onClick={handleExport}
            >
              Export
            </Button>
            
            <Button
              variant="outlined"
              startIcon={<ImportIcon />}
              onClick={() => navigate('/products/import')}
            >
              Import
            </Button>
            
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => navigate('/products/new')}
              size="large"
            >
              Add Product
            </Button>
          </Stack>
        </Box>

        {/* Key Metrics Dashboard */}
        <Grid container spacing={3} sx={{ mb: 2 }}>
          <Grid item xs={12} md={2.4}>
            <Card sx={{ bgcolor: 'primary.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                  <InventoryIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{productData?.summary.total_products || 0}</Typography>
                  <Typography variant="caption" color="text.secondary">Total Products</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2.4}>
            <Card sx={{ bgcolor: 'success.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                  <ActiveIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{productData?.summary.active_products || 0}</Typography>
                  <Typography variant="caption" color="text.secondary">Active Products</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2.4}>
            <Card sx={{ bgcolor: 'warning.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'warning.main', mr: 2 }}>
                  <WarningIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{productData?.summary.low_stock_count || 0}</Typography>
                  <Typography variant="caption" color="text.secondary">Low Stock</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2.4}>
            <Card sx={{ bgcolor: 'error.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'error.main', mr: 2 }}>
                  <WarningIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{productData?.summary.out_of_stock_count || 0}</Typography>
                  <Typography variant="caption" color="text.secondary">Out of Stock</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2.4}>
            <Card sx={{ bgcolor: 'info.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                  <PriceIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">${productData?.summary.total_value?.toFixed(0) || '0'}</Typography>
                  <Typography variant="caption" color="text.secondary">Total Value</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Quick Search */}
        <TextField
          placeholder="Quick search products..."
          value={filters.search}
          onChange={(e) => handleFilterChange('search', e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
          }}
          sx={{ width: 400 }}
        />

        {/* Bulk Actions */}
        {selectedRows.length > 0 && (
          <Card sx={{ mt: 2, bgcolor: 'primary.50' }}>
            <CardContent sx={{ py: 2 }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography>
                  {selectedRows.length} product{selectedRows.length > 1 ? 's' : ''} selected
                </Typography>
                
                <Stack direction="row" spacing={2}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setSelectedRows([])}
                  >
                    Clear Selection
                  </Button>
                  
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<EditIcon />}
                  >
                    Bulk Edit
                  </Button>
                  
                  <Button
                    variant="contained"
                    color="error"
                    size="small"
                    onClick={handleBulkDelete}
                    disabled={deleteMutation.isPending}
                  >
                    Delete Selected
                  </Button>
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        )}
      </Paper>

      {/* Data Grid */}
      <Paper sx={{ flex: 1, overflow: 'hidden' }}>
        {isLoading && <LinearProgress />}
        
        <DataGrid
          rows={productData?.products || []}
          columns={columns}
          paginationModel={paginationModel}
          onPaginationModelChange={setPaginationModel}
          rowCount={productData?.total || 0}
          loading={isLoading}
          checkboxSelection
          disableRowSelectionOnClick
          rowSelectionModel={selectedRows}
          onRowSelectionModelChange={setSelectedRows}
          pageSizeOptions={[10, 25, 50, 100]}
          slots={{
            toolbar: GridToolbar,
          }}
          slotProps={{
            toolbar: {
              showQuickFilter: true,
              quickFilterProps: { debounceMs: 500 },
            },
          }}
          sx={{
            border: 0,
            '& .MuiDataGrid-cell:focus': {
              outline: 'none',
            },
            '& .MuiDataGrid-row:hover': {
              backgroundColor: 'action.hover',
            },
            '& .MuiDataGrid-columnHeaders': {
              backgroundColor: 'grey.50',
              fontSize: '0.875rem',
              fontWeight: 600,
            },
          }}
        />
      </Paper>

      <FilterDrawer />

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            {selectedProduct 
              ? `Are you sure you want to delete "${selectedProduct.name}"?`
              : `Are you sure you want to delete ${selectedRows.length} selected products?`
            }
          </Typography>
          <Typography variant="body2" color="error.main" sx={{ mt: 1 }}>
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={confirmDelete}
            color="error"
            variant="contained"
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ProductListPage;