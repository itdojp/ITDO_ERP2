import React, { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  DataGrid,
  GridColDef,
  GridRowSelectionModel,
  GridToolbar,
  GridActionsCellItem,
  GridRenderCellParams,
} from "@mui/x-data-grid";
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
  Stepper,
  Step,
  StepLabel,
  InputAdornment,
  Tabs,
  Tab,
} from "@mui/material";
import {
  Receipt as ExpenseIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  Download as ExportIcon,
  Upload as UploadIcon,
  AttachFile as AttachIcon,
  CheckCircle as ApprovedIcon,
  Schedule as PendingIcon,
  Cancel as RejectedIcon,
  Assignment as ReportIcon,
  Person as EmployeeIcon,
  Business as BusinessIcon,
  Category as CategoryIcon,
  DateRange as DateIcon,
  AttachMoney as AmountIcon,
  Assessment as AnalyticsIcon,
  AccountBalance as AccountIcon,
  CreditCard as CreditCardIcon,
  LocalDining as MealIcon,
  Flight as TravelIcon,
  DirectionsCar as TransportIcon,
  Hotel as AccommodationIcon,
} from "@mui/icons-material";
import { apiClient } from "@/services/api";

interface Expense {
  id: number;
  expense_number: string;
  employee_id: number;
  employee_name: string;
  department: string;
  category: string;
  subcategory: string;
  description: string;
  amount: number;
  currency: string;
  expense_date: string;
  submitted_date: string;
  status:
    | "draft"
    | "submitted"
    | "under_review"
    | "approved"
    | "rejected"
    | "paid";
  receipt_attached: boolean;
  payment_method: string;
  reimbursable: boolean;
  project_id?: number;
  project_name?: string;
  vendor_name?: string;
  notes?: string;
  approver_id?: number;
  approver_name?: string;
  approved_date?: string;
  rejection_reason?: string;
  created_at: string;
  updated_at: string;
}

interface ExpenseCategory {
  id: number;
  name: string;
  code: string;
  max_amount_per_day?: number;
  requires_receipt: boolean;
  approval_required: boolean;
  account_code: string;
}

interface ExpenseFilters {
  search: string;
  status: string;
  category: string;
  employee_id: string;
  department: string;
  date_from: string;
  date_to: string;
  amount_min: string;
  amount_max: string;
  reimbursable: string;
  has_receipt: string;
}

interface ExpenseSummary {
  total_expenses: number;
  pending_approval: number;
  approved_count: number;
  rejected_count: number;
  paid_count: number;
  total_amount: number;
  pending_amount: number;
  approved_amount: number;
  avg_processing_days: number;
}

interface ExpenseAnalytics {
  category_breakdown: Array<{
    category: string;
    amount: number;
    count: number;
    percentage: number;
  }>;
  monthly_trends: Array<{
    month: string;
    amount: number;
    count: number;
  }>;
  department_expenses: Array<{
    department: string;
    amount: number;
    count: number;
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

export const ExpenseTrackingPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [selectedRows, setSelectedRows] = useState<GridRowSelectionModel>([]);
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false);
  const [approvalDialogOpen, setApprovalDialogOpen] = useState(false);
  const [rejectionDialogOpen, setRejectionDialogOpen] = useState(false);
  const [selectedExpense, setSelectedExpense] = useState<Expense | null>(null);
  const [rejectionReason, setRejectionReason] = useState("");
  const [currentTab, setCurrentTab] = useState(0);

  const [paginationModel, setPaginationModel] = useState({
    page: 0,
    pageSize: 25,
  });

  const [filters, setFilters] = useState<ExpenseFilters>({
    search: "",
    status: "",
    category: "",
    employee_id: "",
    department: "",
    date_from: "",
    date_to: "",
    amount_min: "",
    amount_max: "",
    reimbursable: "",
    has_receipt: "",
  });

  // Mock data for rapid development
  const mockExpenses: Expense[] = [
    {
      id: 1,
      expense_number: "EXP-2024-001",
      employee_id: 201,
      employee_name: "John Smith",
      department: "Sales",
      category: "Travel",
      subcategory: "Airfare",
      description: "Flight to client meeting in NYC",
      amount: 450.0,
      currency: "USD",
      expense_date: "2024-01-15",
      submitted_date: "2024-01-16T09:30:00Z",
      status: "submitted",
      receipt_attached: true,
      payment_method: "Corporate Card",
      reimbursable: false,
      project_id: 101,
      project_name: "Enterprise Sales Q1",
      vendor_name: "Delta Airlines",
      notes: "Business trip for quarterly review meeting",
      created_at: "2024-01-16T09:30:00Z",
      updated_at: "2024-01-16T09:30:00Z",
    },
    {
      id: 2,
      expense_number: "EXP-2024-002",
      employee_id: 202,
      employee_name: "Sarah Johnson",
      department: "Marketing",
      category: "Meals",
      subcategory: "Client Entertainment",
      description: "Lunch meeting with prospective clients",
      amount: 125.5,
      currency: "USD",
      expense_date: "2024-01-14",
      submitted_date: "2024-01-15T14:20:00Z",
      status: "approved",
      receipt_attached: true,
      payment_method: "Personal",
      reimbursable: true,
      vendor_name: "The Capital Grille",
      notes: "Discussing potential partnership opportunities",
      approver_id: 301,
      approver_name: "Michael Davis",
      approved_date: "2024-01-16T10:15:00Z",
      created_at: "2024-01-15T14:20:00Z",
      updated_at: "2024-01-16T10:15:00Z",
    },
    {
      id: 3,
      expense_number: "EXP-2024-003",
      employee_id: 203,
      employee_name: "Robert Chen",
      department: "Engineering",
      category: "Equipment",
      subcategory: "Software License",
      description: "IntelliJ IDEA annual license",
      amount: 199.0,
      currency: "USD",
      expense_date: "2024-01-13",
      submitted_date: "2024-01-13T16:45:00Z",
      status: "paid",
      receipt_attached: true,
      payment_method: "Personal",
      reimbursable: true,
      vendor_name: "JetBrains",
      notes: "Development tools for project work",
      approver_id: 302,
      approver_name: "Lisa Anderson",
      approved_date: "2024-01-14T11:30:00Z",
      created_at: "2024-01-13T16:45:00Z",
      updated_at: "2024-01-17T09:00:00Z",
    },
    {
      id: 4,
      expense_number: "EXP-2024-004",
      employee_id: 204,
      employee_name: "Emily Watson",
      department: "HR",
      category: "Transportation",
      subcategory: "Taxi/Uber",
      description: "Transportation to candidate interviews",
      amount: 45.75,
      currency: "USD",
      expense_date: "2024-01-18",
      submitted_date: "2024-01-18T17:30:00Z",
      status: "under_review",
      receipt_attached: true,
      payment_method: "Personal",
      reimbursable: true,
      vendor_name: "Uber Technologies",
      notes: "Multiple trips for interview coordination",
      created_at: "2024-01-18T17:30:00Z",
      updated_at: "2024-01-18T17:30:00Z",
    },
    {
      id: 5,
      expense_number: "EXP-2024-005",
      employee_id: 205,
      employee_name: "David Wilson",
      department: "Finance",
      category: "Office Supplies",
      subcategory: "Stationary",
      description: "Office supplies for Q1 budget meetings",
      amount: 67.8,
      currency: "USD",
      expense_date: "2024-01-12",
      submitted_date: "2024-01-12T11:20:00Z",
      status: "rejected",
      receipt_attached: false,
      payment_method: "Personal",
      reimbursable: true,
      vendor_name: "Staples",
      notes: "Notebooks, pens, and presentation materials",
      approver_id: 303,
      approver_name: "Jennifer Brown",
      rejection_reason: "Receipt required for reimbursement",
      created_at: "2024-01-12T11:20:00Z",
      updated_at: "2024-01-15T13:45:00Z",
    },
  ];

  // Fetch expenses with mock data
  const {
    data: expenseData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["expenses", filters, paginationModel],
    queryFn: async () => {
      // Simulate API delay
      await new Promise((resolve) => setTimeout(resolve, 800));

      // Filter mock data based on current filters
      let filteredExpenses = mockExpenses;

      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        filteredExpenses = filteredExpenses.filter(
          (expense) =>
            expense.expense_number.toLowerCase().includes(searchLower) ||
            expense.employee_name.toLowerCase().includes(searchLower) ||
            expense.description.toLowerCase().includes(searchLower) ||
            expense.category.toLowerCase().includes(searchLower),
        );
      }

      if (filters.status) {
        filteredExpenses = filteredExpenses.filter(
          (expense) => expense.status === filters.status,
        );
      }

      if (filters.category) {
        filteredExpenses = filteredExpenses.filter(
          (expense) => expense.category === filters.category,
        );
      }

      if (filters.department) {
        filteredExpenses = filteredExpenses.filter(
          (expense) => expense.department === filters.department,
        );
      }

      // Calculate summary
      const summary: ExpenseSummary = {
        total_expenses: mockExpenses.length,
        pending_approval: mockExpenses.filter(
          (e) => e.status === "submitted" || e.status === "under_review",
        ).length,
        approved_count: mockExpenses.filter((e) => e.status === "approved")
          .length,
        rejected_count: mockExpenses.filter((e) => e.status === "rejected")
          .length,
        paid_count: mockExpenses.filter((e) => e.status === "paid").length,
        total_amount: mockExpenses.reduce((sum, e) => sum + e.amount, 0),
        pending_amount: mockExpenses
          .filter(
            (e) => e.status === "submitted" || e.status === "under_review",
          )
          .reduce((sum, e) => sum + e.amount, 0),
        approved_amount: mockExpenses
          .filter((e) => e.status === "approved")
          .reduce((sum, e) => sum + e.amount, 0),
        avg_processing_days: 3.2,
      };

      return {
        expenses: filteredExpenses,
        total: filteredExpenses.length,
        summary,
      };
    },
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  });

  // Fetch expense analytics
  const { data: analytics } = useQuery({
    queryKey: ["expense-analytics"],
    queryFn: async (): Promise<ExpenseAnalytics> => {
      // Mock analytics data
      await new Promise((resolve) => setTimeout(resolve, 500));

      return {
        category_breakdown: [
          { category: "Travel", amount: 4500, count: 12, percentage: 45.2 },
          { category: "Meals", amount: 2800, count: 18, percentage: 28.1 },
          { category: "Equipment", amount: 1600, count: 8, percentage: 16.0 },
          {
            category: "Transportation",
            amount: 750,
            count: 15,
            percentage: 7.5,
          },
          {
            category: "Office Supplies",
            amount: 320,
            count: 6,
            percentage: 3.2,
          },
        ],
        monthly_trends: [
          { month: "Oct", amount: 8200, count: 34 },
          { month: "Nov", amount: 9500, count: 42 },
          { month: "Dec", amount: 7800, count: 28 },
          { month: "Jan", amount: 9970, count: 59 },
        ],
        department_expenses: [
          { department: "Sales", amount: 12500, count: 25 },
          { department: "Marketing", amount: 8900, count: 19 },
          { department: "Engineering", amount: 6700, count: 14 },
          { department: "HR", amount: 3200, count: 11 },
          { department: "Finance", amount: 4670, count: 8 },
        ],
      };
    },
  });

  // Approve/Reject mutations
  const approveMutation = useMutation({
    mutationFn: async (expenseIds: number[]) => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      console.log("Approving expenses:", expenseIds);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
      setApprovalDialogOpen(false);
      setSelectedRows([]);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: async ({
      expenseIds,
      reason,
    }: {
      expenseIds: number[];
      reason: string;
    }) => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      console.log("Rejecting expenses:", expenseIds, "Reason:", reason);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
      setRejectionDialogOpen(false);
      setRejectionReason("");
      setSelectedRows([]);
    },
  });

  // DataGrid columns with advanced features
  const columns: GridColDef[] = useMemo(
    () => [
      {
        field: "expense_number",
        headerName: "Expense #",
        width: 140,
        renderCell: (params: GridRenderCellParams) => (
          <Typography
            variant="body2"
            fontFamily="monospace"
            fontWeight="medium"
            color="primary"
            sx={{ cursor: "pointer" }}
            onClick={() => navigate(`/expenses/${params.row.id}`)}
          >
            {params.value}
          </Typography>
        ),
      },
      {
        field: "employee_name",
        headerName: "Employee",
        width: 160,
        renderCell: (params: GridRenderCellParams) => (
          <Box display="flex" alignItems="center" gap={1}>
            <Avatar sx={{ width: 32, height: 32, bgcolor: "primary.main" }}>
              <EmployeeIcon />
            </Avatar>
            <Box>
              <Typography variant="body2" fontWeight="medium" noWrap>
                {params.value}
              </Typography>
              <Typography variant="caption" color="text.secondary" noWrap>
                {params.row.department}
              </Typography>
            </Box>
          </Box>
        ),
      },
      {
        field: "category",
        headerName: "Category",
        width: 140,
        renderCell: (params: GridRenderCellParams) => {
          const categoryIcons = {
            Travel: <TravelIcon />,
            Meals: <MealIcon />,
            Transportation: <TransportIcon />,
            Equipment: <BusinessIcon />,
            "Office Supplies": <CategoryIcon />,
          };

          return (
            <Chip
              label={params.value}
              size="small"
              variant="outlined"
              color="primary"
              icon={
                categoryIcons[params.value as keyof typeof categoryIcons] || (
                  <CategoryIcon />
                )
              }
            />
          );
        },
      },
      {
        field: "description",
        headerName: "Description",
        width: 250,
        renderCell: (params: GridRenderCellParams) => (
          <Box>
            <Typography variant="body2" fontWeight="medium" noWrap>
              {params.value}
            </Typography>
            <Typography variant="caption" color="text.secondary" noWrap>
              {params.row.vendor_name && `Vendor: ${params.row.vendor_name}`}
            </Typography>
          </Box>
        ),
      },
      {
        field: "amount",
        headerName: "Amount",
        width: 120,
        type: "number",
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
        field: "expense_date",
        headerName: "Date",
        width: 120,
        renderCell: (params: GridRenderCellParams) => (
          <Typography variant="body2">
            {new Date(params.value).toLocaleDateString()}
          </Typography>
        ),
      },
      {
        field: "status",
        headerName: "Status",
        width: 140,
        renderCell: (params: GridRenderCellParams) => {
          const statusConfig = {
            draft: { color: "default" as const, icon: <EditIcon /> },
            submitted: { color: "info" as const, icon: <PendingIcon /> },
            under_review: { color: "warning" as const, icon: <PendingIcon /> },
            approved: { color: "success" as const, icon: <ApprovedIcon /> },
            rejected: { color: "error" as const, icon: <RejectedIcon /> },
            paid: { color: "success" as const, icon: <CheckCircleIcon /> },
          };

          const config =
            statusConfig[params.value as keyof typeof statusConfig];

          return (
            <Chip
              label={params.value.replace("_", " ").toUpperCase()}
              size="small"
              color={config.color}
              variant="filled"
              icon={config.icon}
            />
          );
        },
      },
      {
        field: "receipt_attached",
        headerName: "Receipt",
        width: 100,
        renderCell: (params: GridRenderCellParams) => (
          <Chip
            label={params.value ? "Yes" : "No"}
            size="small"
            color={params.value ? "success" : "error"}
            variant="outlined"
            icon={params.value ? <AttachIcon /> : undefined}
          />
        ),
      },
      {
        field: "reimbursable",
        headerName: "Reimbursable",
        width: 120,
        renderCell: (params: GridRenderCellParams) => (
          <Chip
            label={params.value ? "Yes" : "No"}
            size="small"
            color={params.value ? "primary" : "default"}
            variant="outlined"
          />
        ),
      },
      {
        field: "actions",
        type: "actions",
        headerName: "Actions",
        width: 180,
        getActions: (params) => {
          const actions = [
            <GridActionsCellItem
              icon={<ViewIcon />}
              label="View"
              onClick={() => navigate(`/expenses/${params.id}`)}
              showInMenu
            />,
            <GridActionsCellItem
              icon={<EditIcon />}
              label="Edit"
              onClick={() => navigate(`/expenses/${params.id}/edit`)}
              showInMenu
            />,
          ];

          // Add approval actions for managers/admins
          if (
            params.row.status === "submitted" ||
            params.row.status === "under_review"
          ) {
            actions.push(
              <GridActionsCellItem
                icon={<ApprovedIcon />}
                label="Approve"
                onClick={() => handleApproveSingle(params.row)}
                showInMenu
              />,
              <GridActionsCellItem
                icon={<RejectedIcon />}
                label="Reject"
                onClick={() => handleRejectSingle(params.row)}
                color="error"
                showInMenu
              />,
            );
          }

          actions.push(
            <GridActionsCellItem
              icon={<DeleteIcon />}
              label="Delete"
              onClick={() => handleDeleteSingle(params.row)}
              color="error"
              showInMenu
            />,
          );

          return actions;
        },
      },
    ],
    [navigate],
  );

  // Event handlers
  const handleFilterChange = (field: keyof ExpenseFilters, value: string) => {
    setFilters((prev) => ({ ...prev, [field]: value }));
    setPaginationModel((prev) => ({ ...prev, page: 0 }));
  };

  const handleClearFilters = () => {
    setFilters({
      search: "",
      status: "",
      category: "",
      employee_id: "",
      department: "",
      date_from: "",
      date_to: "",
      amount_min: "",
      amount_max: "",
      reimbursable: "",
      has_receipt: "",
    });
  };

  const handleApproveSingle = (expense: Expense) => {
    setSelectedExpense(expense);
    setApprovalDialogOpen(true);
  };

  const handleRejectSingle = (expense: Expense) => {
    setSelectedExpense(expense);
    setRejectionDialogOpen(true);
  };

  const handleDeleteSingle = (expense: Expense) => {
    console.log("Deleting expense:", expense.id);
    // Implement delete functionality
  };

  const handleBulkApprove = () => {
    if (selectedRows.length > 0) {
      setApprovalDialogOpen(true);
    }
  };

  const handleBulkReject = () => {
    if (selectedRows.length > 0) {
      setRejectionDialogOpen(true);
    }
  };

  const confirmApproval = async () => {
    if (selectedExpense) {
      await approveMutation.mutateAsync([selectedExpense.id]);
    } else if (selectedRows.length > 0) {
      await approveMutation.mutateAsync(selectedRows as number[]);
    }
  };

  const confirmRejection = async () => {
    if (!rejectionReason.trim()) {
      return;
    }

    if (selectedExpense) {
      await rejectMutation.mutateAsync({
        expenseIds: [selectedExpense.id],
        reason: rejectionReason,
      });
    } else if (selectedRows.length > 0) {
      await rejectMutation.mutateAsync({
        expenseIds: selectedRows as number[],
        reason: rejectionReason,
      });
    }
  };

  const handleExport = () => {
    console.log("Exporting expenses with filters:", filters);
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
        Filter Expenses
      </Typography>

      <Stack spacing={3}>
        <TextField
          label="Search"
          placeholder="Search by expense #, employee, description..."
          value={filters.search}
          onChange={(e) => handleFilterChange("search", e.target.value)}
          InputProps={{
            startAdornment: (
              <SearchIcon sx={{ mr: 1, color: "text.secondary" }} />
            ),
          }}
          fullWidth
        />

        <FormControl fullWidth>
          <InputLabel>Status</InputLabel>
          <Select
            value={filters.status}
            onChange={(e) => handleFilterChange("status", e.target.value)}
            label="Status"
          >
            <MenuItem value="">All Status</MenuItem>
            <MenuItem value="draft">Draft</MenuItem>
            <MenuItem value="submitted">Submitted</MenuItem>
            <MenuItem value="under_review">Under Review</MenuItem>
            <MenuItem value="approved">Approved</MenuItem>
            <MenuItem value="rejected">Rejected</MenuItem>
            <MenuItem value="paid">Paid</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>Category</InputLabel>
          <Select
            value={filters.category}
            onChange={(e) => handleFilterChange("category", e.target.value)}
            label="Category"
          >
            <MenuItem value="">All Categories</MenuItem>
            <MenuItem value="Travel">Travel</MenuItem>
            <MenuItem value="Meals">Meals & Entertainment</MenuItem>
            <MenuItem value="Transportation">Transportation</MenuItem>
            <MenuItem value="Equipment">Equipment</MenuItem>
            <MenuItem value="Office Supplies">Office Supplies</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>Department</InputLabel>
          <Select
            value={filters.department}
            onChange={(e) => handleFilterChange("department", e.target.value)}
            label="Department"
          >
            <MenuItem value="">All Departments</MenuItem>
            <MenuItem value="Sales">Sales</MenuItem>
            <MenuItem value="Marketing">Marketing</MenuItem>
            <MenuItem value="Engineering">Engineering</MenuItem>
            <MenuItem value="HR">Human Resources</MenuItem>
            <MenuItem value="Finance">Finance</MenuItem>
          </Select>
        </FormControl>

        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Expense Date Range
          </Typography>
          <Stack direction="row" spacing={2}>
            <TextField
              label="From"
              type="date"
              value={filters.date_from}
              onChange={(e) => handleFilterChange("date_from", e.target.value)}
              size="small"
              InputLabelProps={{ shrink: true }}
            />
            <TextField
              label="To"
              type="date"
              value={filters.date_to}
              onChange={(e) => handleFilterChange("date_to", e.target.value)}
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
              onChange={(e) => handleFilterChange("amount_min", e.target.value)}
              size="small"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">$</InputAdornment>
                ),
              }}
            />
            <TextField
              label="Max Amount"
              type="number"
              value={filters.amount_max}
              onChange={(e) => handleFilterChange("amount_max", e.target.value)}
              size="small"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">$</InputAdornment>
                ),
              }}
            />
          </Stack>
        </Box>

        <FormControl fullWidth>
          <InputLabel>Reimbursable</InputLabel>
          <Select
            value={filters.reimbursable}
            onChange={(e) => handleFilterChange("reimbursable", e.target.value)}
            label="Reimbursable"
          >
            <MenuItem value="">All Expenses</MenuItem>
            <MenuItem value="true">Reimbursable Only</MenuItem>
            <MenuItem value="false">Non-Reimbursable Only</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>Receipt Status</InputLabel>
          <Select
            value={filters.has_receipt}
            onChange={(e) => handleFilterChange("has_receipt", e.target.value)}
            label="Receipt Status"
          >
            <MenuItem value="">All Expenses</MenuItem>
            <MenuItem value="true">With Receipt</MenuItem>
            <MenuItem value="false">Without Receipt</MenuItem>
          </Select>
        </FormControl>

        <Divider />

        <Stack direction="row" spacing={2}>
          <Button variant="outlined" onClick={handleClearFilters} fullWidth>
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

  const activeFiltersCount = Object.values(filters).filter(
    (value) => value !== "",
  ).length;

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">
          Failed to load expenses. Please try again.
          <Button onClick={() => refetch()} sx={{ ml: 2 }}>
            Retry
          </Button>
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 2 }}>
        <Box
          display="flex"
          justifyContent="space-between"
          alignItems="center"
          mb={2}
        >
          <Typography
            variant="h4"
            component="h1"
            sx={{ display: "flex", alignItems: "center", gap: 2 }}
          >
            <Avatar sx={{ bgcolor: "primary.main" }}>
              <ExpenseIcon />
            </Avatar>
            Expense Tracking
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
              onClick={() => navigate("/expenses/new")}
              size="large"
            >
              Add Expense
            </Button>
          </Stack>
        </Box>

        {/* Key Metrics Dashboard */}
        <Grid container spacing={3} sx={{ mb: 2 }}>
          <Grid item xs={12} md={2.4}>
            <Card sx={{ bgcolor: "primary.50" }}>
              <CardContent
                sx={{ display: "flex", alignItems: "center", py: 2 }}
              >
                <Avatar sx={{ bgcolor: "primary.main", mr: 2 }}>
                  <ExpenseIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    {expenseData?.summary.total_expenses || 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Total Expenses
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2.4}>
            <Card sx={{ bgcolor: "warning.50" }}>
              <CardContent
                sx={{ display: "flex", alignItems: "center", py: 2 }}
              >
                <Avatar sx={{ bgcolor: "warning.main", mr: 2 }}>
                  <PendingIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    {expenseData?.summary.pending_approval || 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Pending Approval
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2.4}>
            <Card sx={{ bgcolor: "success.50" }}>
              <CardContent
                sx={{ display: "flex", alignItems: "center", py: 2 }}
              >
                <Avatar sx={{ bgcolor: "success.main", mr: 2 }}>
                  <ApprovedIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    {expenseData?.summary.approved_count || 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Approved
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2.4}>
            <Card sx={{ bgcolor: "info.50" }}>
              <CardContent
                sx={{ display: "flex", alignItems: "center", py: 2 }}
              >
                <Avatar sx={{ bgcolor: "info.main", mr: 2 }}>
                  <AmountIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    ${expenseData?.summary.total_amount?.toFixed(0) || "0"}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Total Amount
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2.4}>
            <Card sx={{ bgcolor: "error.50" }}>
              <CardContent
                sx={{ display: "flex", alignItems: "center", py: 2 }}
              >
                <Avatar sx={{ bgcolor: "error.main", mr: 2 }}>
                  <DateIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    {expenseData?.summary.avg_processing_days?.toFixed(1) ||
                      "0.0"}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Avg Processing Days
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Quick Search */}
        <TextField
          placeholder="Quick search expenses..."
          value={filters.search}
          onChange={(e) => handleFilterChange("search", e.target.value)}
          InputProps={{
            startAdornment: (
              <SearchIcon sx={{ mr: 1, color: "text.secondary" }} />
            ),
          }}
          sx={{ width: 400 }}
        />

        {/* Bulk Actions */}
        {selectedRows.length > 0 && (
          <Card sx={{ mt: 2, bgcolor: "primary.50" }}>
            <CardContent sx={{ py: 2 }}>
              <Stack
                direction="row"
                justifyContent="space-between"
                alignItems="center"
              >
                <Typography>
                  {selectedRows.length} expense
                  {selectedRows.length > 1 ? "s" : ""} selected
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
                    startIcon={<ApprovedIcon />}
                    onClick={handleBulkApprove}
                    color="success"
                  >
                    Approve Selected
                  </Button>

                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<RejectedIcon />}
                    onClick={handleBulkReject}
                    color="error"
                  >
                    Reject Selected
                  </Button>
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        )}
      </Paper>

      {/* Data Grid */}
      <Paper sx={{ flex: 1, overflow: "hidden" }}>
        {isLoading && <LinearProgress />}

        <DataGrid
          rows={expenseData?.expenses || []}
          columns={columns}
          paginationModel={paginationModel}
          onPaginationModelChange={setPaginationModel}
          rowCount={expenseData?.total || 0}
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
            "& .MuiDataGrid-cell:focus": {
              outline: "none",
            },
            "& .MuiDataGrid-row:hover": {
              backgroundColor: "action.hover",
            },
            "& .MuiDataGrid-columnHeaders": {
              backgroundColor: "grey.50",
              fontSize: "0.875rem",
              fontWeight: 600,
            },
          }}
        />
      </Paper>

      <FilterDrawer />

      {/* Approval Dialog */}
      <Dialog
        open={approvalDialogOpen}
        onClose={() => setApprovalDialogOpen(false)}
      >
        <DialogTitle>Approve Expenses</DialogTitle>
        <DialogContent>
          <Typography>
            {selectedExpense
              ? `Approve expense "${selectedExpense.expense_number}" for ${selectedExpense.employee_name}?`
              : `Approve ${selectedRows.length} selected expenses?`}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Approved expenses will be processed for reimbursement.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApprovalDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={confirmApproval}
            color="success"
            variant="contained"
            disabled={approveMutation.isPending}
            startIcon={<ApprovedIcon />}
          >
            {approveMutation.isPending ? "Approving..." : "Approve"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Rejection Dialog */}
      <Dialog
        open={rejectionDialogOpen}
        onClose={() => setRejectionDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Reject Expenses</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            {selectedExpense
              ? `Reject expense "${selectedExpense.expense_number}" for ${selectedExpense.employee_name}?`
              : `Reject ${selectedRows.length} selected expenses?`}
          </Typography>
          <TextField
            label="Rejection Reason"
            placeholder="Please provide a reason for rejection..."
            value={rejectionReason}
            onChange={(e) => setRejectionReason(e.target.value)}
            multiline
            rows={3}
            fullWidth
            margin="normal"
            required
            error={!rejectionReason.trim()}
            helperText={
              !rejectionReason.trim() ? "Rejection reason is required" : ""
            }
          />
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setRejectionDialogOpen(false);
              setRejectionReason("");
            }}
          >
            Cancel
          </Button>
          <Button
            onClick={confirmRejection}
            color="error"
            variant="contained"
            disabled={rejectMutation.isPending || !rejectionReason.trim()}
            startIcon={<RejectedIcon />}
          >
            {rejectMutation.isPending ? "Rejecting..." : "Reject"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ExpenseTrackingPage;
