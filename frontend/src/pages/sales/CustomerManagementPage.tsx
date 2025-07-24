import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataGrid, GridColDef, GridRowSelectionModel, GridToolbar, GridActionsCellItem } from '@mui/x-data-grid';
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  Stack,
  Card,
  CardContent,
  CardHeader,
  Grid,
  Chip,
  Avatar,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Drawer,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  Alert,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  Badge
} from '@mui/material';
import {
  Person as PersonIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  Business as BusinessIcon,
  CreditCard as CreditIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  AttachMoney as MoneyIcon,
  Receipt as OrderIcon,
  Warning as WarningIcon,
  CheckCircle as ActiveIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Download as ExportIcon,
  Refresh as RefreshIcon,
  LocationOn as LocationIcon,
  Stars as VipIcon,
  Schedule as LastOrderIcon
} from '@mui/icons-material';
import { apiClient } from '@/services/api';

interface Customer {
  id: number;
  code: string;
  name: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  country: string;
  tax_id?: string;
  customer_type: 'individual' | 'business';
  status: 'active' | 'inactive' | 'suspended';
  credit_limit: number;
  current_balance: number;
  payment_terms: string;
  discount_rate: number;
  total_orders: number;
  total_spent: number;
  last_order_date?: string;
  created_at: string;
  updated_at: string;
  is_vip: boolean;
  assigned_salesperson?: string;
  notes?: string;
}

interface CustomerTransaction {
  id: number;
  type: 'order' | 'payment' | 'refund' | 'credit_adjustment';
  amount: number;
  date: string;
  reference: string;
  description: string;
  status: 'completed' | 'pending' | 'cancelled';
}

interface CustomerOrder {
  id: number;
  order_number: string;
  date: string;
  status: 'draft' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled';
  total_amount: number;
  items_count: number;
}

interface CustomerFilters {
  search: string;
  status: string;
  customer_type: string;
  payment_terms: string;
  city: string;
  state: string;
  is_vip: string;
  credit_limit_min: string;
  credit_limit_max: string;
  balance_min: string;
  balance_max: string;
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

export const CustomerManagementPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  const [selectedRows, setSelectedRows] = useState<GridRowSelectionModel>([]);
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false);
  const [customerDetailOpen, setCustomerDetailOpen] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [currentTab, setCurrentTab] = useState(0);
  
  const [paginationModel, setPaginationModel] = useState({
    page: 0,
    pageSize: 25,
  });
  
  const [filters, setFilters] = useState<CustomerFilters>({
    search: '',
    status: '',
    customer_type: '',
    payment_terms: '',
    city: '',
    state: '',
    is_vip: '',
    credit_limit_min: '',
    credit_limit_max: '',
    balance_min: '',
    balance_max: ''
  });

  // Fetch customers
  const { data: customerData, isLoading, error, refetch } = useQuery({
    queryKey: ['customers', filters, paginationModel],
    queryFn: async () => {
      const params = new URLSearchParams({
        skip: (paginationModel.page * paginationModel.pageSize).toString(),
        limit: paginationModel.pageSize.toString(),
        sort_by: 'name',
        sort_order: 'asc',
      });

      Object.entries(filters).forEach(([key, value]) => {
        if (value && value !== '') {
          params.append(key, value);
        }
      });

      const response = await apiClient.get(`/api/v1/customers?${params}`);
      return {
        customers: response.data?.customers || [],
        total: response.data?.total || 0,
        active_count: response.data?.active_count || 0,
        total_credit_limit: response.data?.total_credit_limit || 0,
        total_outstanding: response.data?.total_outstanding || 0
      };
    },
  });

  // Fetch customer transactions
  const { data: customerTransactions } = useQuery({
    queryKey: ['customer-transactions', selectedCustomer?.id],
    queryFn: async (): Promise<CustomerTransaction[]> => {
      if (!selectedCustomer) return [];
      const response = await apiClient.get(`/api/v1/customers/${selectedCustomer.id}/transactions`);
      return response.data || [];
    },
    enabled: !!selectedCustomer,
  });

  // Fetch customer orders
  const { data: customerOrders } = useQuery({
    queryKey: ['customer-orders', selectedCustomer?.id],
    queryFn: async (): Promise<CustomerOrder[]> => {
      if (!selectedCustomer) return [];
      const response = await apiClient.get(`/api/v1/customers/${selectedCustomer.id}/orders`);
      return response.data || [];
    },
    enabled: !!selectedCustomer,
  });

  // Delete customers mutation
  const deleteMutation = useMutation({
    mutationFn: async (customerIds: number[]) => {
      await apiClient.post('/api/v1/customers/bulk-delete', { ids: customerIds });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      setSelectedRows([]);
    },
  });

  // Update customer status mutation
  const updateStatusMutation = useMutation({
    mutationFn: async ({ customerId, status }: { customerId: number; status: string }) => {
      await apiClient.patch(`/api/v1/customers/${customerId}`, { status });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
    },
  });

  // DataGrid columns configuration
  const columns: GridColDef[] = useMemo(() => [
    {
      field: 'code',
      headerName: 'Code',
      width: 120,
      renderCell: (params) => (
        <Typography variant="body2" fontFamily="monospace" fontWeight="medium">
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'name',
      headerName: 'Customer',
      width: 200,
      renderCell: (params) => (
        <Box display="flex" alignItems="center" gap={1}>
          <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
            {params.row.customer_type === 'business' ? <BusinessIcon /> : <PersonIcon />}
          </Avatar>
          <Box>
            <Typography variant="body2" fontWeight="medium">
              {params.value}
              {params.row.is_vip && <VipIcon color="warning" sx={{ ml: 0.5, fontSize: 16 }} />}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {params.row.customer_type}
            </Typography>
          </Box>
        </Box>
      ),
    },
    {
      field: 'email',
      headerName: 'Contact',
      width: 200,
      renderCell: (params) => (
        <Box>
          <Typography variant="body2">{params.value}</Typography>
          <Typography variant="caption" color="text.secondary">
            {params.row.phone}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'city',
      headerName: 'Location',
      width: 150,
      renderCell: (params) => (
        <Box>
          <Typography variant="body2">{params.value}</Typography>
          <Typography variant="caption" color="text.secondary">
            {params.row.state}, {params.row.country}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 100,
      renderCell: (params) => (
        <Chip
          label={params.value}
          size="small"
          color={
            params.value === 'active' ? 'success' :
            params.value === 'suspended' ? 'error' :
            'default'
          }
          variant="filled"
        />
      ),
    },
    {
      field: 'credit_limit',
      headerName: 'Credit Limit',
      width: 120,
      type: 'number',
      renderCell: (params) => (
        <Typography variant="body2" fontWeight="medium">
          ${params.value?.toFixed(2) || '0.00'}
        </Typography>
      ),
    },
    {
      field: 'current_balance',
      headerName: 'Balance',
      width: 120,
      type: 'number',
      renderCell: (params) => (
        <Typography 
          variant="body2" 
          fontWeight="medium"
          color={params.value > 0 ? 'error.main' : 'text.primary'}
        >
          ${params.value?.toFixed(2) || '0.00'}
        </Typography>
      ),
    },
    {
      field: 'total_orders',
      headerName: 'Orders',
      width: 100,
      type: 'number',
      renderCell: (params) => (
        <Box textAlign="center">
          <Typography variant="body2" fontWeight="medium">
            {params.value || 0}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            orders
          </Typography>
        </Box>
      ),
    },
    {
      field: 'total_spent',
      headerName: 'Total Spent',
      width: 120,
      type: 'number',
      renderCell: (params) => (
        <Box>
          <Typography variant="body2" fontWeight="medium" color="success.main">
            ${params.value?.toFixed(2) || '0.00'}
          </Typography>
          {params.row.last_order_date && (
            <Typography variant="caption" color="text.secondary">
              Last: {new Date(params.row.last_order_date).toLocaleDateString()}
            </Typography>
          )}
        </Box>
      ),
    },
    {
      field: 'payment_terms',
      headerName: 'Terms',
      width: 100,
      renderCell: (params) => (
        <Chip label={params.value} size="small" variant="outlined" />
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
          onClick={() => {
            setSelectedCustomer(params.row);
            setCustomerDetailOpen(true);
          }}
        />,
        <GridActionsCellItem
          icon={<EditIcon />}
          label="Edit"
          onClick={() => navigate(`/customers/${params.id}/edit`)}
        />,
        <GridActionsCellItem
          icon={<EmailIcon />}
          label="Email"
          onClick={() => window.open(`mailto:${params.row.email}`)}
        />,
        <GridActionsCellItem
          icon={<DeleteIcon />}
          label="Delete"
          onClick={() => handleDeleteCustomer(params.id as number)}
          color="error"
        />,
      ],
    },
  ], [navigate]);

  // Event handlers
  const handleFilterChange = (field: keyof CustomerFilters, value: string) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    setPaginationModel(prev => ({ ...prev, page: 0 }));
  };

  const handleClearFilters = () => {
    setFilters({
      search: '',
      status: '',
      customer_type: '',
      payment_terms: '',
      city: '',
      state: '',
      is_vip: '',
      credit_limit_min: '',
      credit_limit_max: '',
      balance_min: '',
      balance_max: ''
    });
  };

  const handleDeleteCustomer = async (customerId: number) => {
    if (confirm('Are you sure you want to delete this customer?')) {
      await deleteMutation.mutateAsync([customerId]);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedRows.length === 0) return;
    
    if (confirm(`Are you sure you want to delete ${selectedRows.length} customers?`)) {
      await deleteMutation.mutateAsync(selectedRows as number[]);
    }
  };

  const handleExport = () => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value && value !== '') {
        params.append(key, value);
      }
    });
    window.open(`/api/v1/customers/export?${params}`, '_blank');
  };

  // Filter drawer
  const FilterDrawer = () => (
    <Drawer
      anchor="right"
      open={filterDrawerOpen}
      onClose={() => setFilterDrawerOpen(false)}
      PaperProps={{ sx: { width: 400, p: 3 } }}
    >
      <Typography variant="h6" gutterBottom>
        Filter Customers
      </Typography>
      
      <Stack spacing={3}>
        <TextField
          label="Search"
          placeholder="Search by name, email, or code..."
          value={filters.search}
          onChange={(e) => handleFilterChange('search', e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
          }}
          fullWidth
        />

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
            <MenuItem value="suspended">Suspended</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>Customer Type</InputLabel>
          <Select
            value={filters.customer_type}
            onChange={(e) => handleFilterChange('customer_type', e.target.value)}
            label="Customer Type"
          >
            <MenuItem value="">All Types</MenuItem>
            <MenuItem value="individual">Individual</MenuItem>
            <MenuItem value="business">Business</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>Payment Terms</InputLabel>
          <Select
            value={filters.payment_terms}
            onChange={(e) => handleFilterChange('payment_terms', e.target.value)}
            label="Payment Terms"
          >
            <MenuItem value="">All Terms</MenuItem>
            <MenuItem value="COD">Cash on Delivery</MenuItem>
            <MenuItem value="NET15">Net 15 Days</MenuItem>
            <MenuItem value="NET30">Net 30 Days</MenuItem>
            <MenuItem value="NET60">Net 60 Days</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>VIP Status</InputLabel>
          <Select
            value={filters.is_vip}
            onChange={(e) => handleFilterChange('is_vip', e.target.value)}
            label="VIP Status"
          >
            <MenuItem value="">All Customers</MenuItem>
            <MenuItem value="true">VIP Only</MenuItem>
            <MenuItem value="false">Regular Only</MenuItem>
          </Select>
        </FormControl>

        <TextField
          label="City"
          value={filters.city}
          onChange={(e) => handleFilterChange('city', e.target.value)}
          fullWidth
        />

        <TextField
          label="State"
          value={filters.state}
          onChange={(e) => handleFilterChange('state', e.target.value)}
          fullWidth
        />

        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Credit Limit Range
          </Typography>
          <Stack direction="row" spacing={2}>
            <TextField
              label="Min"
              type="number"
              value={filters.credit_limit_min}
              onChange={(e) => handleFilterChange('credit_limit_min', e.target.value)}
              size="small"
            />
            <TextField
              label="Max"
              type="number"
              value={filters.credit_limit_max}
              onChange={(e) => handleFilterChange('credit_limit_max', e.target.value)}
              size="small"
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
          Failed to load customers. Please try again.
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
          <Typography variant="h4" component="h1">
            Customer Management
          </Typography>
          
          <Stack direction="row" spacing={2}>
            <IconButton onClick={() => refetch()} disabled={isLoading}>
              <RefreshIcon />
            </IconButton>
            
            <Button
              variant="outlined"
              startIcon={<FilterIcon />}
              onClick={() => setFilterDrawerOpen(true)}
            >
              Filters {activeFiltersCount > 0 && `(${activeFiltersCount})`}
            </Button>
            
            <Button
              variant="outlined"
              startIcon={<ExportIcon />}
              onClick={handleExport}
            >
              Export
            </Button>
            
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => navigate('/customers/new')}
            >
              Add Customer
            </Button>
          </Stack>
        </Box>

        {/* Key Metrics */}
        <Grid container spacing={3} sx={{ mb: 2 }}>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                  <PersonIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{customerData?.total || 0}</Typography>
                  <Typography variant="caption" color="text.secondary">Total Customers</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                  <ActiveIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{customerData?.active_count || 0}</Typography>
                  <Typography variant="caption" color="text.secondary">Active Customers</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                  <CreditIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">${customerData?.total_credit_limit?.toFixed(0) || '0'}</Typography>
                  <Typography variant="caption" color="text.secondary">Total Credit Limit</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'warning.main', mr: 2 }}>
                  <WarningIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">${customerData?.total_outstanding?.toFixed(0) || '0'}</Typography>
                  <Typography variant="caption" color="text.secondary">Outstanding Balance</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Quick Search */}
        <TextField
          placeholder="Quick search customers..."
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
                  {selectedRows.length} customer{selectedRows.length > 1 ? 's' : ''} selected
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
          rows={customerData?.customers || []}
          columns={columns}
          paginationModel={paginationModel}
          onPaginationModelChange={setPaginationModel}
          rowCount={customerData?.total || 0}
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
          }}
        />
      </Paper>

      <FilterDrawer />

      {/* Customer Detail Dialog */}
      <Dialog
        open={customerDetailOpen}
        onClose={() => setCustomerDetailOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Stack direction="row" alignItems="center" spacing={2}>
            <Avatar sx={{ bgcolor: 'primary.main' }}>
              {selectedCustomer?.customer_type === 'business' ? <BusinessIcon /> : <PersonIcon />}
            </Avatar>
            <Box>
              <Typography variant="h6">
                {selectedCustomer?.name}
                {selectedCustomer?.is_vip && <VipIcon color="warning" sx={{ ml: 1 }} />}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {selectedCustomer?.code} • {selectedCustomer?.customer_type}
              </Typography>
            </Box>
          </Stack>
        </DialogTitle>
        <DialogContent>
          {selectedCustomer && (
            <>
              <Tabs value={currentTab} onChange={(_, newValue) => setCurrentTab(newValue)}>
                <Tab icon={<PersonIcon />} label="Details" />
                <Tab icon={<OrderIcon />} label="Orders" />
                <Tab icon={<MoneyIcon />} label="Transactions" />
              </Tabs>

              {/* Customer Details Tab */}
              <TabPanel value={currentTab} index={0}>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardHeader title="Contact Information" />
                      <CardContent>
                        <Stack spacing={2}>
                          <Box>
                            <Typography variant="subtitle2" color="text.secondary">Email</Typography>
                            <Typography>{selectedCustomer.email}</Typography>
                          </Box>
                          <Box>
                            <Typography variant="subtitle2" color="text.secondary">Phone</Typography>
                            <Typography>{selectedCustomer.phone}</Typography>
                          </Box>
                          <Box>
                            <Typography variant="subtitle2" color="text.secondary">Address</Typography>
                            <Typography>
                              {selectedCustomer.address}<br />
                              {selectedCustomer.city}, {selectedCustomer.state} {selectedCustomer.zip_code}<br />
                              {selectedCustomer.country}
                            </Typography>
                          </Box>
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardHeader title="Account Information" />
                      <CardContent>
                        <Stack spacing={2}>
                          <Box>
                            <Typography variant="subtitle2" color="text.secondary">Status</Typography>
                            <Chip
                              label={selectedCustomer.status}
                              color={
                                selectedCustomer.status === 'active' ? 'success' :
                                selectedCustomer.status === 'suspended' ? 'error' :
                                'default'
                              }
                              size="small"
                            />
                          </Box>
                          <Box>
                            <Typography variant="subtitle2" color="text.secondary">Credit Limit</Typography>
                            <Typography>${selectedCustomer.credit_limit.toFixed(2)}</Typography>
                          </Box>
                          <Box>
                            <Typography variant="subtitle2" color="text.secondary">Current Balance</Typography>
                            <Typography color={selectedCustomer.current_balance > 0 ? 'error.main' : 'text.primary'}>
                              ${selectedCustomer.current_balance.toFixed(2)}
                            </Typography>
                          </Box>
                          <Box>
                            <Typography variant="subtitle2" color="text.secondary">Payment Terms</Typography>
                            <Typography>{selectedCustomer.payment_terms}</Typography>
                          </Box>
                          <Box>
                            <Typography variant="subtitle2" color="text.secondary">Discount Rate</Typography>
                            <Typography>{selectedCustomer.discount_rate}%</Typography>
                          </Box>
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </TabPanel>

              {/* Customer Orders Tab */}
              <TabPanel value={currentTab} index={1}>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Order Number</TableCell>
                        <TableCell>Date</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell align="right">Items</TableCell>
                        <TableCell align="right">Total</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {customerOrders?.map((order) => (
                        <TableRow key={order.id}>
                          <TableCell>{order.order_number}</TableCell>
                          <TableCell>{new Date(order.date).toLocaleDateString()}</TableCell>
                          <TableCell>
                            <Chip
                              label={order.status}
                              size="small"
                              color={
                                order.status === 'delivered' ? 'success' :
                                order.status === 'cancelled' ? 'error' :
                                'warning'
                              }
                            />
                          </TableCell>
                          <TableCell align="right">{order.items_count}</TableCell>
                          <TableCell align="right">${order.total_amount.toFixed(2)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </TabPanel>

              {/* Customer Transactions Tab */}
              <TabPanel value={currentTab} index={2}>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Date</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Description</TableCell>
                        <TableCell>Reference</TableCell>
                        <TableCell align="right">Amount</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {customerTransactions?.map((transaction) => (
                        <TableRow key={transaction.id}>
                          <TableCell>{new Date(transaction.date).toLocaleDateString()}</TableCell>
                          <TableCell>
                            <Chip label={transaction.type} size="small" variant="outlined" />
                          </TableCell>
                          <TableCell>{transaction.description}</TableCell>
                          <TableCell>{transaction.reference}</TableCell>
                          <TableCell align="right">
                            <Typography
                              color={
                                transaction.type === 'payment' || transaction.type === 'refund' ?
                                'success.main' : 'text.primary'
                              }
                            >
                              ${transaction.amount.toFixed(2)}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={transaction.status}
                              size="small"
                              color={
                                transaction.status === 'completed' ? 'success' :
                                transaction.status === 'cancelled' ? 'error' :
                                'warning'
                              }
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </TabPanel>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCustomerDetailOpen(false)}>Close</Button>
          <Button
            variant="contained"
            startIcon={<EditIcon />}
            onClick={() => {
              navigate(`/customers/${selectedCustomer?.id}/edit`);
              setCustomerDetailOpen(false);
            }}
          >
            Edit Customer
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CustomerManagementPage;