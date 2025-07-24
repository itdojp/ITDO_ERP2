import React, { useState, useMemo } from 'react';
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
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Autocomplete,
  InputAdornment
} from '@mui/material';
import {
  Receipt as InvoiceIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  Download as ExportIcon,
  Email as EmailIcon,
  Print as PrintIcon,
  Send as SendIcon,
  AttachMoney as MoneyIcon,
  Person as CustomerIcon,
  Business as BusinessIcon,
  CheckCircle as PaidIcon,
  Schedule as PendingIcon,
  Warning as OverdueIcon,
  Cancel as CancelledIcon,
  PictureAsPdf as PdfIcon,
  ContentCopy as CopyIcon,
  Payment as PaymentIcon,
  Calculate as TotalIcon
} from '@mui/icons-material';
import { apiClient } from '@/services/api';

interface Invoice {
  id: number;
  invoice_number: string;
  customer_id: number;
  customer_name: string;
  customer_email: string;
  issue_date: string;
  due_date: string;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  subtotal: number;
  tax_amount: number;
  discount_amount: number;
  total_amount: number;
  paid_amount: number;
  balance_due: number;
  payment_terms: string;
  currency: string;
  created_at: string;
  updated_at: string;
  last_sent_date?: string;
  paid_date?: string;
  notes?: string;
}

interface InvoiceItem {
  id?: number;
  product_id: number;
  product_name: string;
  description: string;
  quantity: number;
  unit_price: number;
  tax_rate: number;
  discount_rate: number;
  line_total: number;
}

interface Customer {
  id: number;
  name: string;
  email: string;
  address: string;
  payment_terms: string;
  tax_id?: string;
}

interface InvoiceFilters {
  search: string;
  status: string;
  customer_id: string;
  date_from: string;
  date_to: string;
  amount_min: string;
  amount_max: string;
  payment_terms: string;
  overdue_only: string;
}

interface InvoiceSummary {
  total_invoices: number;
  draft_count: number;
  sent_count: number;
  paid_count: number;
  overdue_count: number;
  total_amount: number;
  paid_amount: number;
  outstanding_amount: number;
  avg_days_to_pay: number;
}

export const InvoiceManagementPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  const [selectedRows, setSelectedRows] = useState<GridRowSelectionModel>([]);
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [sendDialogOpen, setSendDialogOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  
  const [paginationModel, setPaginationModel] = useState({
    page: 0,
    pageSize: 25,
  });
  
  const [filters, setFilters] = useState<InvoiceFilters>({
    search: '',
    status: '',
    customer_id: '',
    date_from: '',
    date_to: '',
    amount_min: '',
    amount_max: '',
    payment_terms: '',
    overdue_only: ''
  });

  // Mock data for rapid development
  const mockInvoices: Invoice[] = [
    {
      id: 1,
      invoice_number: 'INV-2024-001',
      customer_id: 101,
      customer_name: 'TechCorp Solutions Ltd',
      customer_email: 'billing@techcorp.com',
      issue_date: '2024-01-15',
      due_date: '2024-02-14',
      status: 'sent',
      subtotal: 12500.00,
      tax_amount: 1250.00,
      discount_amount: 250.00,
      total_amount: 13500.00,
      paid_amount: 0,
      balance_due: 13500.00,
      payment_terms: 'NET30',
      currency: 'USD',
      created_at: '2024-01-15T09:00:00Z',
      updated_at: '2024-01-15T14:30:00Z',
      last_sent_date: '2024-01-15T14:30:00Z',
      notes: 'Monthly consulting services'
    },
    {
      id: 2,
      invoice_number: 'INV-2024-002',
      customer_id: 102,
      customer_name: 'Global Industries Inc',
      customer_email: 'accounts@globalind.com',
      issue_date: '2024-01-10',
      due_date: '2024-01-25',
      status: 'overdue',
      subtotal: 8750.00,
      tax_amount: 875.00,
      discount_amount: 0,
      total_amount: 9625.00,
      paid_amount: 0,
      balance_due: 9625.00,
      payment_terms: 'NET15',
      currency: 'USD',
      created_at: '2024-01-10T10:15:00Z',
      updated_at: '2024-01-10T16:45:00Z',
      last_sent_date: '2024-01-10T16:45:00Z',
      notes: 'Software license renewal'
    },
    {
      id: 3,
      invoice_number: 'INV-2024-003',
      customer_id: 103,
      customer_name: 'Innovative Systems LLC',
      customer_email: 'finance@innosys.com',
      issue_date: '2024-01-20',
      due_date: '2024-02-19',
      status: 'paid',
      subtotal: 15600.00,
      tax_amount: 1560.00,
      discount_amount: 780.00,
      total_amount: 16380.00,
      paid_amount: 16380.00,
      balance_due: 0,
      payment_terms: 'NET30',
      currency: 'USD',
      created_at: '2024-01-20T11:30:00Z',
      updated_at: '2024-01-22T09:15:00Z',
      paid_date: '2024-01-22T09:15:00Z',
      notes: 'Custom development project'
    },
    {
      id: 4,
      invoice_number: 'INV-2024-004',
      customer_id: 104,
      customer_name: 'Digital Ventures Co',
      customer_email: 'billing@digitalventures.com',
      issue_date: '2024-01-18',
      due_date: '2024-02-02',
      status: 'draft',
      subtotal: 6200.00,
      tax_amount: 620.00,
      discount_amount: 124.00,
      total_amount: 6696.00,
      paid_amount: 0,
      balance_due: 6696.00,
      payment_terms: 'NET15',
      currency: 'USD',
      created_at: '2024-01-18T13:45:00Z',
      updated_at: '2024-01-18T13:45:00Z',
      notes: 'Web design services'
    },
    {
      id: 5,
      invoice_number: 'INV-2024-005',
      customer_id: 105,
      customer_name: 'Enterprise Analytics Corp',
      customer_email: 'payments@enterpriseanalytics.com',
      issue_date: '2024-01-12',
      due_date: '2024-02-11',
      status: 'sent',
      subtotal: 22000.00,
      tax_amount: 2200.00,
      discount_amount: 1100.00,
      total_amount: 23100.00,
      paid_amount: 11550.00,
      balance_due: 11550.00,
      payment_terms: 'NET30',
      currency: 'USD',
      created_at: '2024-01-12T08:20:00Z',
      updated_at: '2024-01-16T14:10:00Z',
      last_sent_date: '2024-01-12T08:20:00Z',
      notes: 'Data analytics platform implementation - 50% partial payment received'
    }
  ];

  // Fetch invoices with mock data
  const { data: invoiceData, isLoading, error, refetch } = useQuery({
    queryKey: ['invoices', filters, paginationModel],
    queryFn: async () => {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Filter mock data based on current filters
      let filteredInvoices = mockInvoices;
      
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        filteredInvoices = filteredInvoices.filter(invoice => 
          invoice.invoice_number.toLowerCase().includes(searchLower) ||
          invoice.customer_name.toLowerCase().includes(searchLower) ||
          invoice.customer_email.toLowerCase().includes(searchLower)
        );
      }
      
      if (filters.status) {
        filteredInvoices = filteredInvoices.filter(invoice => invoice.status === filters.status);
      }
      
      if (filters.overdue_only === 'true') {
        filteredInvoices = filteredInvoices.filter(invoice => invoice.status === 'overdue');
      }
      
      // Calculate summary
      const summary: InvoiceSummary = {
        total_invoices: mockInvoices.length,
        draft_count: mockInvoices.filter(i => i.status === 'draft').length,
        sent_count: mockInvoices.filter(i => i.status === 'sent').length,
        paid_count: mockInvoices.filter(i => i.status === 'paid').length,
        overdue_count: mockInvoices.filter(i => i.status === 'overdue').length,
        total_amount: mockInvoices.reduce((sum, i) => sum + i.total_amount, 0),
        paid_amount: mockInvoices.reduce((sum, i) => sum + i.paid_amount, 0),
        outstanding_amount: mockInvoices.reduce((sum, i) => sum + i.balance_due, 0),
        avg_days_to_pay: 18.5
      };
      
      return {
        invoices: filteredInvoices,
        total: filteredInvoices.length,
        summary
      };
    },
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  });

  // Delete mutation (mocked)
  const deleteMutation = useMutation({
    mutationFn: async (invoiceIds: number[]) => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      console.log('Deleting invoices:', invoiceIds);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      setSelectedRows([]);
      setDeleteDialogOpen(false);
    },
  });

  // Send invoice mutation (mocked)
  const sendInvoiceMutation = useMutation({
    mutationFn: async (invoiceIds: number[]) => {
      await new Promise(resolve => setTimeout(resolve, 1500));
      console.log('Sending invoices:', invoiceIds);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      setSendDialogOpen(false);
    },
  });

  // DataGrid columns with advanced features
  const columns: GridColDef[] = useMemo(() => [
    {
      field: 'invoice_number',
      headerName: 'Invoice #',
      width: 140,
      renderCell: (params: GridRenderCellParams) => (
        <Typography 
          variant="body2" 
          fontFamily="monospace" 
          fontWeight="medium" 
          color="primary"
          sx={{ cursor: 'pointer' }}
          onClick={() => navigate(`/invoices/${params.row.id}`)}
        >
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'customer_name',
      headerName: 'Customer',
      width: 220,
      renderCell: (params: GridRenderCellParams) => (
        <Box>
          <Typography variant="body2" fontWeight="medium" noWrap>
            {params.value}
          </Typography>
          <Typography variant="caption" color="text.secondary" noWrap>
            {params.row.customer_email}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'issue_date',
      headerName: 'Issue Date',
      width: 120,
      renderCell: (params: GridRenderCellParams) => (
        <Typography variant="body2">
          {new Date(params.value).toLocaleDateString()}
        </Typography>
      ),
    },
    {
      field: 'due_date',
      headerName: 'Due Date',
      width: 120,
      renderCell: (params: GridRenderCellParams) => {
        const isOverdue = new Date(params.value) < new Date() && params.row.status !== 'paid';
        return (
          <Typography 
            variant="body2" 
            color={isOverdue ? 'error.main' : 'text.primary'}
            fontWeight={isOverdue ? 'medium' : 'normal'}
          >
            {new Date(params.value).toLocaleDateString()}
          </Typography>
        );
      },
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params: GridRenderCellParams) => {
        const statusConfig = {
          draft: { color: 'default' as const, icon: <EditIcon /> },
          sent: { color: 'info' as const, icon: <SendIcon /> },
          paid: { color: 'success' as const, icon: <PaidIcon /> },
          overdue: { color: 'error' as const, icon: <OverdueIcon /> },
          cancelled: { color: 'default' as const, icon: <CancelledIcon /> }
        };
        
        const config = statusConfig[params.value as keyof typeof statusConfig];
        
        return (
          <Chip
            label={params.value.toUpperCase()}
            size="small"
            color={config.color}
            variant="filled"
            icon={config.icon}
          />
        );
      },
    },
    {
      field: 'total_amount',
      headerName: 'Total Amount',
      width: 140,
      type: 'number',
      renderCell: (params: GridRenderCellParams) => (
        <Box textAlign="right">
          <Typography variant="body2" fontWeight="bold" color="primary.main">
            ${params.value.toFixed(2)}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {params.row.currency}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'balance_due',
      headerName: 'Balance Due',
      width: 140,
      type: 'number',
      renderCell: (params: GridRenderCellParams) => {
        const balanceDue = params.value as number;
        return (
          <Box textAlign="right">
            <Typography 
              variant="body2" 
              fontWeight="bold"
              color={balanceDue > 0 ? 'error.main' : 'success.main'}
            >
              ${balanceDue.toFixed(2)}
            </Typography>
            {balanceDue > 0 && (
              <Typography variant="caption" color="text.secondary">
                Outstanding
              </Typography>
            )}
          </Box>
        );
      },
    },
    {
      field: 'payment_terms',
      headerName: 'Terms',
      width: 100,
      renderCell: (params: GridRenderCellParams) => (
        <Chip 
          label={params.value} 
          size="small" 
          variant="outlined" 
          color="primary"
        />
      ),
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 180,
      getActions: (params) => [
        <GridActionsCellItem
          icon={<ViewIcon />}
          label="View"
          onClick={() => navigate(`/invoices/${params.id}`)}
          showInMenu
        />,
        <GridActionsCellItem
          icon={<EditIcon />}
          label="Edit"
          onClick={() => navigate(`/invoices/${params.id}/edit`)}
          showInMenu
        />,
        <GridActionsCellItem
          icon={<PdfIcon />}
          label="Download PDF"
          onClick={() => handleDownloadPdf(params.row)}
          showInMenu
        />,
        <GridActionsCellItem
          icon={<EmailIcon />}
          label="Send Email"
          onClick={() => handleSendSingle(params.row)}
          showInMenu
        />,
        <GridActionsCellItem
          icon={<CopyIcon />}
          label="Duplicate"
          onClick={() => handleDuplicate(params.row)}
          showInMenu
        />,
        <GridActionsCellItem
          icon={<PaymentIcon />}
          label="Record Payment"
          onClick={() => handleRecordPayment(params.row)}
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
  const handleFilterChange = (field: keyof InvoiceFilters, value: string) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    setPaginationModel(prev => ({ ...prev, page: 0 }));
  };

  const handleClearFilters = () => {
    setFilters({
      search: '',
      status: '',
      customer_id: '',
      date_from: '',
      date_to: '',
      amount_min: '',
      amount_max: '',
      payment_terms: '',
      overdue_only: ''
    });
  };

  const handleDeleteSingle = (invoice: Invoice) => {
    setSelectedInvoice(invoice);
    setDeleteDialogOpen(true);
  };

  const handleSendSingle = (invoice: Invoice) => {
    setSelectedInvoice(invoice);
    setSendDialogOpen(true);
  };

  const handleBulkDelete = () => {
    if (selectedRows.length > 0) {
      setDeleteDialogOpen(true);
    }
  };

  const handleBulkSend = () => {
    if (selectedRows.length > 0) {
      setSendDialogOpen(true);
    }
  };

  const confirmDelete = async () => {
    if (selectedInvoice) {
      await deleteMutation.mutateAsync([selectedInvoice.id]);
    } else if (selectedRows.length > 0) {
      await deleteMutation.mutateAsync(selectedRows as number[]);
    }
  };

  const confirmSend = async () => {
    if (selectedInvoice) {
      await sendInvoiceMutation.mutateAsync([selectedInvoice.id]);
    } else if (selectedRows.length > 0) {
      await sendInvoiceMutation.mutateAsync(selectedRows as number[]);
    }
  };

  const handleDownloadPdf = (invoice: Invoice) => {
    window.open(`/api/v1/invoices/${invoice.id}/pdf`, '_blank');
  };

  const handleDuplicate = (invoice: Invoice) => {
    navigate('/invoices/new', { state: { duplicateFrom: invoice.id } });
  };

  const handleRecordPayment = (invoice: Invoice) => {
    navigate(`/invoices/${invoice.id}/payment`);
  };

  const handleExport = () => {
    console.log('Exporting invoices with filters:', filters);
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
        Filter Invoices
      </Typography>
      
      <Stack spacing={3}>
        <TextField
          label="Search"
          placeholder="Search by invoice #, customer..."
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
            <MenuItem value="draft">Draft</MenuItem>
            <MenuItem value="sent">Sent</MenuItem>
            <MenuItem value="paid">Paid</MenuItem>
            <MenuItem value="overdue">Overdue</MenuItem>
            <MenuItem value="cancelled">Cancelled</MenuItem>
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
            <MenuItem value="NET15">Net 15 Days</MenuItem>
            <MenuItem value="NET30">Net 30 Days</MenuItem>
            <MenuItem value="NET60">Net 60 Days</MenuItem>
            <MenuItem value="COD">Cash on Delivery</MenuItem>
          </Select>
        </FormControl>

        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Issue Date Range
          </Typography>
          <Stack direction="row" spacing={2}>
            <TextField
              label="From"
              type="date"
              value={filters.date_from}
              onChange={(e) => handleFilterChange('date_from', e.target.value)}
              size="small"
              InputLabelProps={{ shrink: true }}
            />
            <TextField
              label="To"
              type="date"
              value={filters.date_to}
              onChange={(e) => handleFilterChange('date_to', e.target.value)}
              size="small"
              InputLabelProps={{ shrink: true }}
            />
          </Stack>
        </Box>

        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Amount Range
          </Typography>
          <Stack direction="row" spacing={2}>
            <TextField
              label="Min Amount"
              type="number"
              value={filters.amount_min}
              onChange={(e) => handleFilterChange('amount_min', e.target.value)}
              size="small"
              InputProps={{ startAdornment: <InputAdornment position="start">$</InputAdornment> }}
            />
            <TextField
              label="Max Amount"
              type="number"
              value={filters.amount_max}
              onChange={(e) => handleFilterChange('amount_max', e.target.value)}
              size="small"
              InputProps={{ startAdornment: <InputAdornment position="start">$</InputAdornment> }}
            />
          </Stack>
        </Box>
        
        <FormControl fullWidth>
          <InputLabel>Show Overdue Only</InputLabel>
          <Select
            value={filters.overdue_only}
            onChange={(e) => handleFilterChange('overdue_only', e.target.value)}
            label="Show Overdue Only"
          >
            <MenuItem value="">All Invoices</MenuItem>
            <MenuItem value="true">Overdue Only</MenuItem>
          </Select>
        </FormControl>

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
          Failed to load invoices. Please try again.
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
              <InvoiceIcon />
            </Avatar>
            Invoice Management
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
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => navigate('/invoices/new')}
              size="large"
            >
              Create Invoice
            </Button>
          </Stack>
        </Box>

        {/* Key Metrics Dashboard */}
        <Grid container spacing={3} sx={{ mb: 2 }}>
          <Grid item xs={12} md={2.4}>
            <Card sx={{ bgcolor: 'primary.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                  <InvoiceIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{invoiceData?.summary.total_invoices || 0}</Typography>
                  <Typography variant="caption" color="text.secondary">Total Invoices</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2.4}>
            <Card sx={{ bgcolor: 'success.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                  <PaidIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{invoiceData?.summary.paid_count || 0}</Typography>
                  <Typography variant="caption" color="text.secondary">Paid Invoices</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2.4}>
            <Card sx={{ bgcolor: 'error.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'error.main', mr: 2 }}>
                  <OverdueIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{invoiceData?.summary.overdue_count || 0}</Typography>
                  <Typography variant="caption" color="text.secondary">Overdue</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2.4}>
            <Card sx={{ bgcolor: 'info.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                  <TotalIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">${invoiceData?.summary.total_amount?.toFixed(0) || '0'}</Typography>
                  <Typography variant="caption" color="text.secondary">Total Amount</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2.4}>
            <Card sx={{ bgcolor: 'warning.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'warning.main', mr: 2 }}>
                  <MoneyIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">${invoiceData?.summary.outstanding_amount?.toFixed(0) || '0'}</Typography>
                  <Typography variant="caption" color="text.secondary">Outstanding</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Quick Search */}
        <TextField
          placeholder="Quick search invoices..."
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
                  {selectedRows.length} invoice{selectedRows.length > 1 ? 's' : ''} selected
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
                    startIcon={<EmailIcon />}
                    onClick={handleBulkSend}
                  >
                    Send Selected
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
          rows={invoiceData?.invoices || []}
          columns={columns}
          paginationModel={paginationModel}
          onPaginationModelChange={setPaginationModel}
          rowCount={invoiceData?.total || 0}
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
            {selectedInvoice 
              ? `Are you sure you want to delete invoice "${selectedInvoice.invoice_number}"?`
              : `Are you sure you want to delete ${selectedRows.length} selected invoices?`
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

      {/* Send Invoice Dialog */}
      <Dialog open={sendDialogOpen} onClose={() => setSendDialogOpen(false)}>
        <DialogTitle>Send Invoice</DialogTitle>
        <DialogContent>
          <Typography>
            {selectedInvoice 
              ? `Send invoice "${selectedInvoice.invoice_number}" to ${selectedInvoice.customer_email}?`
              : `Send ${selectedRows.length} selected invoices to their respective customers?`
            }
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Invoices will be sent via email as PDF attachments.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSendDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={confirmSend}
            color="primary"
            variant="contained"
            disabled={sendInvoiceMutation.isPending}
            startIcon={<EmailIcon />}
          >
            {sendInvoiceMutation.isPending ? 'Sending...' : 'Send'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default InvoiceManagementPage;