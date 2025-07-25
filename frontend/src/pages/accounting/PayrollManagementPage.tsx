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
  CardHeader,
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
  Tabs,
  Tab,
  InputAdornment,
  Stepper,
  Step,
  StepLabel,
} from "@mui/material";
import {
  AccountBalance as PayrollIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  Download as ExportIcon,
  Print as PrintIcon,
  Email as EmailIcon,
  AttachMoney as SalaryIcon,
  Person as EmployeeIcon,
  Business as DepartmentIcon,
  Calculate as CalculateIcon,
  Schedule as PeriodIcon,
  CheckCircle as ProcessedIcon,
  Pending as PendingIcon,
  Cancel as CancelledIcon,
  Receipt as PayslipIcon,
  Assignment as ReportIcon,
  AccountBalanceWallet as BankIcon,
  CreditCard as PaymentIcon,
  TrendingUp as BonusIcon,
  Remove as DeductionIcon,
  LocalAtm as CashIcon,
  Security as BenefitsIcon,
  Assessment as TaxIcon,
  DateRange as DateIcon,
} from "@mui/icons-material";
import { apiClient } from "@/services/api";

interface PayrollRecord {
  id: number;
  payroll_number: string;
  employee_id: number;
  employee_name: string;
  employee_code: string;
  department: string;
  position: string;
  pay_period_start: string;
  pay_period_end: string;
  pay_date: string;
  status:
    | "draft"
    | "calculated"
    | "approved"
    | "processed"
    | "paid"
    | "cancelled";
  base_salary: number;
  overtime_hours: number;
  overtime_rate: number;
  overtime_pay: number;
  bonuses: number;
  commissions: number;
  allowances: number;
  gross_pay: number;
  federal_tax: number;
  state_tax: number;
  social_security: number;
  medicare: number;
  health_insurance: number;
  retirement_contribution: number;
  other_deductions: number;
  total_deductions: number;
  net_pay: number;
  currency: string;
  payment_method: "direct_deposit" | "check" | "cash";
  bank_account: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  processed_by?: string;
  processed_date?: string;
}

interface Employee {
  id: number;
  employee_code: string;
  name: string;
  department: string;
  position: string;
  hire_date: string;
  salary_base: number;
  hourly_rate?: number;
  overtime_eligible: boolean;
  tax_status: string;
  exemptions: number;
  direct_deposit: boolean;
  bank_account?: string;
}

interface PayrollFilters {
  search: string;
  status: string;
  department: string;
  pay_period: string;
  employee_id: string;
  payment_method: string;
  amount_min: string;
  amount_max: string;
}

interface PayrollSummary {
  total_records: number;
  total_employees: number;
  total_gross_pay: number;
  total_net_pay: number;
  total_taxes: number;
  total_deductions: number;
  processed_count: number;
  pending_count: number;
  avg_net_pay: number;
}

interface PayrollAnalytics {
  department_breakdown: Array<{
    department: string;
    employee_count: number;
    total_gross: number;
    total_net: number;
    avg_salary: number;
  }>;
  monthly_trends: Array<{
    month: string;
    total_payroll: number;
    employee_count: number;
    avg_per_employee: number;
  }>;
  tax_breakdown: Array<{
    tax_type: string;
    amount: number;
    percentage_of_gross: number;
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

export const PayrollManagementPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [selectedRows, setSelectedRows] = useState<GridRowSelectionModel>([]);
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false);
  const [processDialogOpen, setProcessDialogOpen] = useState(false);
  const [payslipDialogOpen, setPayslipDialogOpen] = useState(false);
  const [selectedPayroll, setSelectedPayroll] = useState<PayrollRecord | null>(
    null,
  );
  const [currentTab, setCurrentTab] = useState(0);

  const [paginationModel, setPaginationModel] = useState({
    page: 0,
    pageSize: 25,
  });

  const [filters, setFilters] = useState<PayrollFilters>({
    search: "",
    status: "",
    department: "",
    pay_period: "",
    employee_id: "",
    payment_method: "",
    amount_min: "",
    amount_max: "",
  });

  // Mock data for rapid development
  const mockPayrollRecords: PayrollRecord[] = [
    {
      id: 1,
      payroll_number: "PAY-2024-001",
      employee_id: 301,
      employee_name: "John Smith",
      employee_code: "EMP-001",
      department: "Engineering",
      position: "Senior Software Engineer",
      pay_period_start: "2024-01-01",
      pay_period_end: "2024-01-15",
      pay_date: "2024-01-20",
      status: "processed",
      base_salary: 5000.0,
      overtime_hours: 8,
      overtime_rate: 75.0,
      overtime_pay: 600.0,
      bonuses: 1000.0,
      commissions: 0,
      allowances: 200.0,
      gross_pay: 6800.0,
      federal_tax: 1360.0,
      state_tax: 340.0,
      social_security: 421.6,
      medicare: 98.6,
      health_insurance: 250.0,
      retirement_contribution: 340.0,
      other_deductions: 50.0,
      total_deductions: 2860.2,
      net_pay: 3939.8,
      currency: "USD",
      payment_method: "direct_deposit",
      bank_account: "****1234",
      notes: "Performance bonus included",
      created_at: "2024-01-18T09:00:00Z",
      updated_at: "2024-01-20T14:30:00Z",
      processed_by: "HR Admin",
      processed_date: "2024-01-20T14:30:00Z",
    },
    {
      id: 2,
      payroll_number: "PAY-2024-002",
      employee_id: 302,
      employee_name: "Sarah Johnson",
      employee_code: "EMP-002",
      department: "Marketing",
      position: "Marketing Manager",
      pay_period_start: "2024-01-01",
      pay_period_end: "2024-01-15",
      pay_date: "2024-01-20",
      status: "approved",
      base_salary: 4500.0,
      overtime_hours: 0,
      overtime_rate: 0,
      overtime_pay: 0,
      bonuses: 500.0,
      commissions: 750.0,
      allowances: 150.0,
      gross_pay: 5900.0,
      federal_tax: 1180.0,
      state_tax: 295.0,
      social_security: 365.8,
      medicare: 85.55,
      health_insurance: 300.0,
      retirement_contribution: 295.0,
      other_deductions: 25.0,
      total_deductions: 2546.35,
      net_pay: 3353.65,
      currency: "USD",
      payment_method: "direct_deposit",
      bank_account: "****5678",
      notes: "Commission from Q4 sales",
      created_at: "2024-01-18T10:15:00Z",
      updated_at: "2024-01-19T16:20:00Z",
    },
    {
      id: 3,
      payroll_number: "PAY-2024-003",
      employee_id: 303,
      employee_name: "Robert Chen",
      employee_code: "EMP-003",
      department: "Finance",
      position: "Financial Analyst",
      pay_period_start: "2024-01-01",
      pay_period_end: "2024-01-15",
      pay_date: "2024-01-20",
      status: "calculated",
      base_salary: 3800.0,
      overtime_hours: 4,
      overtime_rate: 57.5,
      overtime_pay: 230.0,
      bonuses: 0,
      commissions: 0,
      allowances: 100.0,
      gross_pay: 4130.0,
      federal_tax: 826.0,
      state_tax: 206.5,
      social_security: 256.06,
      medicare: 59.89,
      health_insurance: 275.0,
      retirement_contribution: 206.5,
      other_deductions: 0,
      total_deductions: 1829.95,
      net_pay: 2300.05,
      currency: "USD",
      payment_method: "direct_deposit",
      bank_account: "****9012",
      created_at: "2024-01-18T11:30:00Z",
      updated_at: "2024-01-18T11:30:00Z",
    },
    {
      id: 4,
      payroll_number: "PAY-2024-004",
      employee_id: 304,
      employee_name: "Emily Watson",
      employee_code: "EMP-004",
      department: "HR",
      position: "HR Specialist",
      pay_period_start: "2024-01-01",
      pay_period_end: "2024-01-15",
      pay_date: "2024-01-20",
      status: "draft",
      base_salary: 3500.0,
      overtime_hours: 0,
      overtime_rate: 0,
      overtime_pay: 0,
      bonuses: 250.0,
      commissions: 0,
      allowances: 75.0,
      gross_pay: 3825.0,
      federal_tax: 765.0,
      state_tax: 191.25,
      social_security: 237.15,
      medicare: 55.46,
      health_insurance: 225.0,
      retirement_contribution: 191.25,
      other_deductions: 15.0,
      total_deductions: 1680.11,
      net_pay: 2144.89,
      currency: "USD",
      payment_method: "check",
      bank_account: "",
      created_at: "2024-01-18T13:45:00Z",
      updated_at: "2024-01-18T13:45:00Z",
    },
    {
      id: 5,
      payroll_number: "PAY-2024-005",
      employee_id: 305,
      employee_name: "David Wilson",
      employee_code: "EMP-005",
      department: "Sales",
      position: "Sales Representative",
      pay_period_start: "2024-01-01",
      pay_period_end: "2024-01-15",
      pay_date: "2024-01-20",
      status: "paid",
      base_salary: 2800.0,
      overtime_hours: 6,
      overtime_rate: 42.0,
      overtime_pay: 252.0,
      bonuses: 0,
      commissions: 1200.0,
      allowances: 50.0,
      gross_pay: 4302.0,
      federal_tax: 860.4,
      state_tax: 215.1,
      social_security: 266.72,
      medicare: 62.38,
      health_insurance: 200.0,
      retirement_contribution: 215.1,
      other_deductions: 30.0,
      total_deductions: 1849.7,
      net_pay: 2452.3,
      currency: "USD",
      payment_method: "direct_deposit",
      bank_account: "****3456",
      notes: "High commission month",
      created_at: "2024-01-18T14:20:00Z",
      updated_at: "2024-01-21T10:00:00Z",
      processed_by: "Payroll System",
      processed_date: "2024-01-21T10:00:00Z",
    },
  ];

  // Fetch payroll records with mock data
  const {
    data: payrollData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["payroll-records", filters, paginationModel],
    queryFn: async () => {
      // Simulate API delay
      await new Promise((resolve) => setTimeout(resolve, 800));

      // Filter mock data based on current filters
      let filteredRecords = mockPayrollRecords;

      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        filteredRecords = filteredRecords.filter(
          (record) =>
            record.payroll_number.toLowerCase().includes(searchLower) ||
            record.employee_name.toLowerCase().includes(searchLower) ||
            record.employee_code.toLowerCase().includes(searchLower) ||
            record.department.toLowerCase().includes(searchLower),
        );
      }

      if (filters.status) {
        filteredRecords = filteredRecords.filter(
          (record) => record.status === filters.status,
        );
      }

      if (filters.department) {
        filteredRecords = filteredRecords.filter(
          (record) => record.department === filters.department,
        );
      }

      // Calculate summary
      const summary: PayrollSummary = {
        total_records: mockPayrollRecords.length,
        total_employees: new Set(mockPayrollRecords.map((r) => r.employee_id))
          .size,
        total_gross_pay: mockPayrollRecords.reduce(
          (sum, r) => sum + r.gross_pay,
          0,
        ),
        total_net_pay: mockPayrollRecords.reduce(
          (sum, r) => sum + r.net_pay,
          0,
        ),
        total_taxes: mockPayrollRecords.reduce(
          (sum, r) =>
            sum + r.federal_tax + r.state_tax + r.social_security + r.medicare,
          0,
        ),
        total_deductions: mockPayrollRecords.reduce(
          (sum, r) => sum + r.total_deductions,
          0,
        ),
        processed_count: mockPayrollRecords.filter(
          (r) => r.status === "processed" || r.status === "paid",
        ).length,
        pending_count: mockPayrollRecords.filter(
          (r) => r.status === "draft" || r.status === "calculated",
        ).length,
        avg_net_pay:
          mockPayrollRecords.reduce((sum, r) => sum + r.net_pay, 0) /
          mockPayrollRecords.length,
      };

      return {
        records: filteredRecords,
        total: filteredRecords.length,
        summary,
      };
    },
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  });

  // Fetch analytics
  const { data: analytics } = useQuery({
    queryKey: ["payroll-analytics"],
    queryFn: async (): Promise<PayrollAnalytics> => {
      // Mock analytics data
      await new Promise((resolve) => setTimeout(resolve, 500));

      return {
        department_breakdown: [
          {
            department: "Engineering",
            employee_count: 15,
            total_gross: 102000,
            total_net: 71400,
            avg_salary: 6800,
          },
          {
            department: "Sales",
            employee_count: 12,
            total_gross: 86400,
            total_net: 60480,
            avg_salary: 7200,
          },
          {
            department: "Marketing",
            employee_count: 8,
            total_gross: 47200,
            total_net: 33040,
            avg_salary: 5900,
          },
          {
            department: "Finance",
            employee_count: 6,
            total_gross: 24780,
            total_net: 17346,
            avg_salary: 4130,
          },
          {
            department: "HR",
            employee_count: 4,
            total_gross: 15300,
            total_net: 10710,
            avg_salary: 3825,
          },
        ],
        monthly_trends: [
          {
            month: "Oct",
            total_payroll: 245000,
            employee_count: 42,
            avg_per_employee: 5833,
          },
          {
            month: "Nov",
            total_payroll: 258000,
            employee_count: 43,
            avg_per_employee: 6000,
          },
          {
            month: "Dec",
            total_payroll: 275000,
            employee_count: 44,
            avg_per_employee: 6250,
          },
          {
            month: "Jan",
            total_payroll: 275680,
            employee_count: 45,
            avg_per_employee: 6127,
          },
        ],
        tax_breakdown: [
          { tax_type: "Federal Tax", amount: 55126, percentage_of_gross: 20.0 },
          { tax_type: "State Tax", amount: 13782, percentage_of_gross: 5.0 },
          {
            tax_type: "Social Security",
            amount: 17082,
            percentage_of_gross: 6.2,
          },
          { tax_type: "Medicare", amount: 3996, percentage_of_gross: 1.45 },
        ],
      };
    },
  });

  // Process payroll mutation
  const processMutation = useMutation({
    mutationFn: async (recordIds: number[]) => {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      console.log("Processing payroll records:", recordIds);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["payroll-records"] });
      setProcessDialogOpen(false);
      setSelectedRows([]);
    },
  });

  // DataGrid columns with advanced features
  const columns: GridColDef[] = useMemo(
    () => [
      {
        field: "payroll_number",
        headerName: "Payroll #",
        width: 140,
        renderCell: (params: GridRenderCellParams) => (
          <Typography
            variant="body2"
            fontFamily="monospace"
            fontWeight="medium"
            color="primary"
            sx={{ cursor: "pointer" }}
            onClick={() => navigate(`/payroll/${params.row.id}`)}
          >
            {params.value}
          </Typography>
        ),
      },
      {
        field: "employee_name",
        headerName: "Employee",
        width: 180,
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
                {params.row.employee_code} • {params.row.position}
              </Typography>
            </Box>
          </Box>
        ),
      },
      {
        field: "department",
        headerName: "Department",
        width: 120,
        renderCell: (params: GridRenderCellParams) => (
          <Chip
            label={params.value}
            size="small"
            variant="outlined"
            color="primary"
            icon={<DepartmentIcon />}
          />
        ),
      },
      {
        field: "pay_period_end",
        headerName: "Pay Period",
        width: 140,
        renderCell: (params: GridRenderCellParams) => (
          <Box>
            <Typography variant="body2" fontWeight="medium">
              {new Date(params.row.pay_period_start).toLocaleDateString()} -
            </Typography>
            <Typography variant="body2">
              {new Date(params.value).toLocaleDateString()}
            </Typography>
          </Box>
        ),
      },
      {
        field: "gross_pay",
        headerName: "Gross Pay",
        width: 130,
        type: "number",
        renderCell: (params: GridRenderCellParams) => (
          <Box textAlign="right">
            <Typography variant="body2" fontWeight="bold" color="success.main">
              ${params.value.toFixed(2)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {params.row.currency}
            </Typography>
          </Box>
        ),
      },
      {
        field: "total_deductions",
        headerName: "Deductions",
        width: 130,
        type: "number",
        renderCell: (params: GridRenderCellParams) => (
          <Box textAlign="right">
            <Typography variant="body2" fontWeight="medium" color="error.main">
              -${params.value.toFixed(2)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Total
            </Typography>
          </Box>
        ),
      },
      {
        field: "net_pay",
        headerName: "Net Pay",
        width: 130,
        type: "number",
        renderCell: (params: GridRenderCellParams) => (
          <Box textAlign="right">
            <Typography variant="body2" fontWeight="bold" color="primary.main">
              ${params.value.toFixed(2)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Take Home
            </Typography>
          </Box>
        ),
      },
      {
        field: "status",
        headerName: "Status",
        width: 120,
        renderCell: (params: GridRenderCellParams) => {
          const statusConfig = {
            draft: { color: "default" as const, icon: <EditIcon /> },
            calculated: { color: "info" as const, icon: <CalculateIcon /> },
            approved: { color: "warning" as const, icon: <CheckCircleIcon /> },
            processed: { color: "success" as const, icon: <ProcessedIcon /> },
            paid: { color: "success" as const, icon: <CashIcon /> },
            cancelled: { color: "error" as const, icon: <CancelledIcon /> },
          };

          const config =
            statusConfig[params.value as keyof typeof statusConfig];

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
        field: "payment_method",
        headerName: "Payment",
        width: 140,
        renderCell: (params: GridRenderCellParams) => {
          const methodIcons = {
            direct_deposit: <BankIcon />,
            check: <PaymentIcon />,
            cash: <CashIcon />,
          };

          return (
            <Box display="flex" alignItems="center" gap={1}>
              {methodIcons[params.value as keyof typeof methodIcons]}
              <Box>
                <Typography variant="body2" fontWeight="medium">
                  {params.value.replace("_", " ").toUpperCase()}
                </Typography>
                {params.row.bank_account && (
                  <Typography variant="caption" color="text.secondary">
                    {params.row.bank_account}
                  </Typography>
                )}
              </Box>
            </Box>
          );
        },
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
              label="View Details"
              onClick={() => navigate(`/payroll/${params.id}`)}
              showInMenu
            />,
            <GridActionsCellItem
              icon={<EditIcon />}
              label="Edit"
              onClick={() => navigate(`/payroll/${params.id}/edit`)}
              showInMenu
            />,
            <GridActionsCellItem
              icon={<PayslipIcon />}
              label="Generate Payslip"
              onClick={() => handleGeneratePayslip(params.row)}
              showInMenu
            />,
          ];

          // Add process action for calculated records
          if (
            params.row.status === "calculated" ||
            params.row.status === "approved"
          ) {
            actions.push(
              <GridActionsCellItem
                icon={<ProcessedIcon />}
                label="Process Payment"
                onClick={() => handleProcessSingle(params.row)}
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
  const handleFilterChange = (field: keyof PayrollFilters, value: string) => {
    setFilters((prev) => ({ ...prev, [field]: value }));
    setPaginationModel((prev) => ({ ...prev, page: 0 }));
  };

  const handleClearFilters = () => {
    setFilters({
      search: "",
      status: "",
      department: "",
      pay_period: "",
      employee_id: "",
      payment_method: "",
      amount_min: "",
      amount_max: "",
    });
  };

  const handleProcessSingle = (payroll: PayrollRecord) => {
    setSelectedPayroll(payroll);
    setProcessDialogOpen(true);
  };

  const handleGeneratePayslip = (payroll: PayrollRecord) => {
    setSelectedPayroll(payroll);
    setPayslipDialogOpen(true);
  };

  const handleDeleteSingle = (payroll: PayrollRecord) => {
    console.log("Deleting payroll record:", payroll.id);
    // Implement delete functionality
  };

  const handleBulkProcess = () => {
    if (selectedRows.length > 0) {
      setProcessDialogOpen(true);
    }
  };

  const confirmProcess = async () => {
    if (selectedPayroll) {
      await processMutation.mutateAsync([selectedPayroll.id]);
    } else if (selectedRows.length > 0) {
      await processMutation.mutateAsync(selectedRows as number[]);
    }
  };

  const generatePayslipPdf = () => {
    if (selectedPayroll) {
      window.open(
        `/api/v1/payroll/${selectedPayroll.id}/payslip.pdf`,
        "_blank",
      );
    }
    setPayslipDialogOpen(false);
  };

  const emailPayslip = () => {
    if (selectedPayroll) {
      console.log("Emailing payslip for:", selectedPayroll.employee_name);
      // Implement email functionality
    }
    setPayslipDialogOpen(false);
  };

  const handleExport = () => {
    console.log("Exporting payroll records with filters:", filters);
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
        Filter Payroll Records
      </Typography>

      <Stack spacing={3}>
        <TextField
          label="Search"
          placeholder="Search by payroll #, employee, code..."
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
            <MenuItem value="calculated">Calculated</MenuItem>
            <MenuItem value="approved">Approved</MenuItem>
            <MenuItem value="processed">Processed</MenuItem>
            <MenuItem value="paid">Paid</MenuItem>
            <MenuItem value="cancelled">Cancelled</MenuItem>
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
            <MenuItem value="Engineering">Engineering</MenuItem>
            <MenuItem value="Sales">Sales</MenuItem>
            <MenuItem value="Marketing">Marketing</MenuItem>
            <MenuItem value="Finance">Finance</MenuItem>
            <MenuItem value="HR">Human Resources</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>Payment Method</InputLabel>
          <Select
            value={filters.payment_method}
            onChange={(e) =>
              handleFilterChange("payment_method", e.target.value)
            }
            label="Payment Method"
          >
            <MenuItem value="">All Methods</MenuItem>
            <MenuItem value="direct_deposit">Direct Deposit</MenuItem>
            <MenuItem value="check">Check</MenuItem>
            <MenuItem value="cash">Cash</MenuItem>
          </Select>
        </FormControl>

        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Net Pay Range
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
          Failed to load payroll records. Please try again.
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
              <PayrollIcon />
            </Avatar>
            Payroll Management
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
              startIcon={<ReportIcon />}
              onClick={() => navigate("/payroll/reports")}
            >
              Reports
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
              onClick={() => navigate("/payroll/new")}
              size="large"
            >
              Run Payroll
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
                  <EmployeeIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    {payrollData?.summary.total_employees || 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Employees
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
                  <SalaryIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    ${payrollData?.summary.total_gross_pay?.toFixed(0) || "0"}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Total Gross Pay
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
                  <CashIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    ${payrollData?.summary.total_net_pay?.toFixed(0) || "0"}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Total Net Pay
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
                  <TaxIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    ${payrollData?.summary.total_taxes?.toFixed(0) || "0"}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Total Taxes
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
                    {payrollData?.summary.pending_count || 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Pending
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Quick Search */}
        <TextField
          placeholder="Quick search payroll records..."
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
                  {selectedRows.length} record
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
                    variant="contained"
                    size="small"
                    startIcon={<ProcessedIcon />}
                    onClick={handleBulkProcess}
                    color="success"
                  >
                    Process Selected
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
          rows={payrollData?.records || []}
          columns={columns}
          paginationModel={paginationModel}
          onPaginationModelChange={setPaginationModel}
          rowCount={payrollData?.total || 0}
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

      {/* Process Payment Dialog */}
      <Dialog
        open={processDialogOpen}
        onClose={() => setProcessDialogOpen(false)}
      >
        <DialogTitle>Process Payroll</DialogTitle>
        <DialogContent>
          <Typography>
            {selectedPayroll
              ? `Process payroll for ${selectedPayroll.employee_name} (${selectedPayroll.payroll_number})?`
              : `Process ${selectedRows.length} selected payroll records?`}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This will mark the payroll as processed and ready for payment
            distribution.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setProcessDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={confirmProcess}
            color="success"
            variant="contained"
            disabled={processMutation.isPending}
            startIcon={<ProcessedIcon />}
          >
            {processMutation.isPending ? "Processing..." : "Process"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Payslip Dialog */}
      <Dialog
        open={payslipDialogOpen}
        onClose={() => setPayslipDialogOpen(false)}
      >
        <DialogTitle>Generate Payslip</DialogTitle>
        <DialogContent>
          <Typography>
            Generate payslip for {selectedPayroll?.employee_name} (
            {selectedPayroll?.payroll_number})?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Choose how you want to deliver the payslip.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPayslipDialogOpen(false)}>Cancel</Button>
          <Button onClick={emailPayslip} startIcon={<EmailIcon />}>
            Email
          </Button>
          <Button
            onClick={generatePayslipPdf}
            variant="contained"
            startIcon={<PrintIcon />}
          >
            Download PDF
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PayrollManagementPage;
