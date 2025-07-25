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
  Switch,
  FormControlLabel,
  Checkbox,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Person as UserIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  Download as ExportIcon,
  Email as EmailIcon,
  Lock as LockIcon,
  LockOpen as UnlockIcon,
  Security as SecurityIcon,
  AdminPanelSettings as AdminIcon,
  People as GroupIcon,
  Business as CompanyIcon,
  CheckCircle as ActiveIcon,
  Cancel as InactiveIcon,
  Schedule as PendingIcon,
  Shield as PermissionIcon,
  Key as RoleIcon,
  Settings as SettingsIcon,
  History as ActivityIcon,
  Notifications as NotificationIcon,
  VpnKey as AuthIcon,
  ExpandMore as ExpandMoreIcon,
  SupervisorAccount as SupervisorIcon,
  Work as WorkIcon,
  AccountBox as ProfileIcon
} from '@mui/icons-material';
import { apiClient } from '@/services/api';

interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  avatar_url?: string;
  phone?: string;
  department: string;
  position: string;
  manager_id?: number;
  manager_name?: string;
  status: 'active' | 'inactive' | 'pending' | 'suspended';
  is_admin: boolean;
  is_superuser: boolean;
  roles: string[];
  permissions: string[];
  last_login?: string;
  login_count: number;
  password_expires_at?: string;
  two_factor_enabled: boolean;
  email_verified: boolean;
  created_at: string;
  updated_at: string;
  last_activity?: string;
}

interface Role {
  id: number;
  name: string;
  code: string;
  description: string;
  is_system_role: boolean;
  permissions: Permission[];
  user_count: number;
  created_at: string;
}

interface Permission {
  id: number;
  name: string;
  code: string;
  description: string;
  category: string;
  is_dangerous: boolean;
}

interface UserFilters {
  search: string;
  status: string;
  department: string;
  role: string;
  is_admin: string;
  last_login_days: string;
  email_verified: string;
  two_factor_enabled: string;
}

interface UserSummary {
  total_users: number;
  active_users: number;
  admin_users: number;
  pending_users: number;
  suspended_users: number;
  unverified_emails: number;
  without_2fa: number;
  avg_login_frequency: number;
}

interface UserActivity {
  id: number;
  user_id: number;
  action: string;
  description: string;
  ip_address: string;
  user_agent: string;
  timestamp: string;
  risk_level: 'low' | 'medium' | 'high';
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

export const UserManagementPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  const [selectedRows, setSelectedRows] = useState<GridRowSelectionModel>([]);
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false);
  const [userDetailOpen, setUserDetailOpen] = useState(false);
  const [roleManagementOpen, setRoleManagementOpen] = useState(false);
  const [bulkActionOpen, setBulkActionOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [currentTab, setCurrentTab] = useState(0);
  const [bulkAction, setBulkAction] = useState('');
  
  const [paginationModel, setPaginationModel] = useState({
    page: 0,
    pageSize: 25,
  });
  
  const [filters, setFilters] = useState<UserFilters>({
    search: '',
    status: '',
    department: '',
    role: '',
    is_admin: '',
    last_login_days: '',
    email_verified: '',
    two_factor_enabled: ''
  });

  // Mock data for rapid development
  const mockUsers: User[] = [
    {
      id: 1,
      username: 'john.smith',
      email: 'john.smith@company.com',
      first_name: 'John',
      last_name: 'Smith',
      full_name: 'John Smith',
      avatar_url: '/avatars/john.jpg',
      phone: '+1-555-0123',
      department: 'Engineering',
      position: 'Senior Software Engineer',
      manager_id: 5,
      manager_name: 'Alice Johnson',
      status: 'active',
      is_admin: false,
      is_superuser: false,
      roles: ['Developer', 'Code Reviewer'],
      permissions: ['read_code', 'write_code', 'review_code', 'deploy_dev'],
      last_login: '2024-01-20T14:30:00Z',
      login_count: 234,
      password_expires_at: '2024-07-15T00:00:00Z',
      two_factor_enabled: true,
      email_verified: true,
      created_at: '2023-03-15T09:00:00Z',
      updated_at: '2024-01-20T14:30:00Z',
      last_activity: '2024-01-20T16:45:00Z'
    },
    {
      id: 2,
      username: 'sarah.johnson',
      email: 'sarah.johnson@company.com',
      first_name: 'Sarah',
      last_name: 'Johnson',
      full_name: 'Sarah Johnson',
      phone: '+1-555-0124',
      department: 'Marketing',
      position: 'Marketing Manager',
      status: 'active',
      is_admin: true,
      is_superuser: false,
      roles: ['Marketing Manager', 'Content Admin'],
      permissions: ['manage_marketing', 'create_campaigns', 'view_analytics', 'manage_content'],
      last_login: '2024-01-20T09:15:00Z',
      login_count: 186,
      password_expires_at: '2024-06-20T00:00:00Z',
      two_factor_enabled: true,
      email_verified: true,
      created_at: '2023-01-10T10:30:00Z',
      updated_at: '2024-01-20T09:15:00Z',
      last_activity: '2024-01-20T15:20:00Z'
    },
    {
      id: 3,
      username: 'robert.chen',
      email: 'robert.chen@company.com',
      first_name: 'Robert',
      last_name: 'Chen',
      full_name: 'Robert Chen',
      phone: '+1-555-0125',
      department: 'Finance',
      position: 'Financial Analyst',
      manager_id: 6,
      manager_name: 'David Wilson',
      status: 'active',
      is_admin: false,
      is_superuser: false,
      roles: ['Finance User', 'Report Viewer'],
      permissions: ['view_financials', 'create_reports', 'approve_expenses'],
      last_login: '2024-01-19T16:45:00Z',
      login_count: 98,
      password_expires_at: '2024-05-10T00:00:00Z',
      two_factor_enabled: false,
      email_verified: true,
      created_at: '2023-06-01T14:20:00Z',
      updated_at: '2024-01-19T16:45:00Z',
      last_activity: '2024-01-19T17:30:00Z'
    },
    {
      id: 4,
      username: 'emily.watson',
      email: 'emily.watson@company.com',
      first_name: 'Emily',
      last_name: 'Watson',
      full_name: 'Emily Watson',
      phone: '+1-555-0126',
      department: 'HR',
      position: 'HR Specialist',
      status: 'pending',
      is_admin: false,
      is_superuser: false,
      roles: ['HR User'],
      permissions: ['view_employees', 'manage_timeoff'],
      login_count: 0,
      password_expires_at: '2024-08-01T00:00:00Z',
      two_factor_enabled: false,
      email_verified: false,
      created_at: '2024-01-18T11:00:00Z',
      updated_at: '2024-01-18T11:00:00Z'
    },
    {
      id: 5,
      username: 'alice.johnson',
      email: 'alice.johnson@company.com',
      first_name: 'Alice',
      last_name: 'Johnson',
      full_name: 'Alice Johnson',
      phone: '+1-555-0127',
      department: 'Engineering',
      position: 'Engineering Manager',
      status: 'active',
      is_admin: true,
      is_superuser: true,
      roles: ['Engineering Manager', 'System Admin'],
      permissions: ['manage_users', 'system_config', 'deploy_prod', 'manage_team'],
      last_login: '2024-01-20T08:00:00Z',
      login_count: 412,
      password_expires_at: '2024-09-15T00:00:00Z',
      two_factor_enabled: true,
      email_verified: true,
      created_at: '2022-11-01T09:00:00Z',
      updated_at: '2024-01-20T08:00:00Z',
      last_activity: '2024-01-20T17:00:00Z'
    }
  ];

  const mockRoles: Role[] = [
    {
      id: 1,
      name: 'System Administrator',
      code: 'SYSTEM_ADMIN',
      description: 'Full system access with all administrative privileges',
      is_system_role: true,
      permissions: [],
      user_count: 2,
      created_at: '2022-01-01T00:00:00Z'
    },
    {
      id: 2,
      name: 'Engineering Manager',
      code: 'ENG_MANAGER',
      description: 'Manage engineering team and technical resources',
      is_system_role: false,
      permissions: [],
      user_count: 3,
      created_at: '2022-01-01T00:00:00Z'
    },
    {
      id: 3,
      name: 'Developer',
      code: 'DEVELOPER',
      description: 'Software development and code review access',
      is_system_role: false,
      permissions: [],
      user_count: 12,
      created_at: '2022-01-01T00:00:00Z'
    },
    {
      id: 4,
      name: 'Marketing Manager',
      code: 'MARKETING_MANAGER',
      description: 'Marketing campaigns and content management',
      is_system_role: false,
      permissions: [],
      user_count: 4,
      created_at: '2022-01-01T00:00:00Z'
    },
    {
      id: 5,
      name: 'Finance User',
      code: 'FINANCE_USER',
      description: 'Financial data access and reporting',
      is_system_role: false,
      permissions: [],
      user_count: 6,
      created_at: '2022-01-01T00:00:00Z'
    }
  ];

  // Fetch users with mock data
  const { data: userData, isLoading, error, refetch } = useQuery({
    queryKey: ['users', filters, paginationModel],
    queryFn: async () => {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Filter mock data based on current filters
      let filteredUsers = mockUsers;
      
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        filteredUsers = filteredUsers.filter(user => 
          user.full_name.toLowerCase().includes(searchLower) ||
          user.email.toLowerCase().includes(searchLower) ||
          user.username.toLowerCase().includes(searchLower) ||
          user.department.toLowerCase().includes(searchLower)
        );
      }
      
      if (filters.status) {
        filteredUsers = filteredUsers.filter(user => user.status === filters.status);
      }
      
      if (filters.department) {
        filteredUsers = filteredUsers.filter(user => user.department === filters.department);
      }
      
      if (filters.is_admin === 'true') {
        filteredUsers = filteredUsers.filter(user => user.is_admin);
      } else if (filters.is_admin === 'false') {
        filteredUsers = filteredUsers.filter(user => !user.is_admin);
      }
      
      // Calculate summary
      const summary: UserSummary = {
        total_users: mockUsers.length,
        active_users: mockUsers.filter(u => u.status === 'active').length,
        admin_users: mockUsers.filter(u => u.is_admin).length,
        pending_users: mockUsers.filter(u => u.status === 'pending').length,
        suspended_users: mockUsers.filter(u => u.status === 'suspended').length,
        unverified_emails: mockUsers.filter(u => !u.email_verified).length,
        without_2fa: mockUsers.filter(u => !u.two_factor_enabled).length,
        avg_login_frequency: mockUsers.reduce((sum, u) => sum + u.login_count, 0) / mockUsers.length
      };
      
      return {
        users: filteredUsers,
        total: filteredUsers.length,
        summary
      };
    },
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  });

  // Fetch roles
  const { data: rolesData } = useQuery({
    queryKey: ['roles'],
    queryFn: async () => {
      await new Promise(resolve => setTimeout(resolve, 400));
      return mockRoles;
    },
  });

  // Bulk action mutation
  const bulkActionMutation = useMutation({
    mutationFn: async ({ action, userIds }: { action: string; userIds: number[] }) => {
      await new Promise(resolve => setTimeout(resolve, 1500));
      console.log('Bulk action:', action, 'on users:', userIds);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setBulkActionOpen(false);
      setSelectedRows([]);
    },
  });

  // DataGrid columns with advanced features
  const columns: GridColDef[] = useMemo(() => [
    {
      field: 'avatar',
      headerName: '',
      width: 60,
      sortable: false,
      filterable: false,
      renderCell: (params: GridRenderCellParams) => (
        <Avatar
          src={params.row.avatar_url}
          sx={{ width: 36, height: 36 }}
        >
          {params.row.first_name?.[0]}{params.row.last_name?.[0]}
        </Avatar>
      ),
    },
    {
      field: 'full_name',
      headerName: 'User',
      width: 200,
      renderCell: (params: GridRenderCellParams) => (
        <Box>
          <Typography variant="body2" fontWeight="medium" noWrap>
            {params.value}
            {params.row.is_superuser && <SupervisorIcon color="error" sx={{ ml: 0.5, fontSize: 16 }} />}
            {params.row.is_admin && !params.row.is_superuser && <AdminIcon color="warning" sx={{ ml: 0.5, fontSize: 16 }} />}
          </Typography>
          <Typography variant="caption" color="text.secondary" noWrap>
            @{params.row.username} • {params.row.email}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'department',
      headerName: 'Department',
      width: 140,
      renderCell: (params: GridRenderCellParams) => (
        <Box>
          <Typography variant="body2" fontWeight="medium">
            {params.value}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {params.row.position}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'roles',
      headerName: 'Roles',
      width: 200,
      renderCell: (params: GridRenderCellParams) => (
        <Stack direction="row" spacing={0.5} flexWrap="wrap">
          {params.value.slice(0, 2).map((role: string, index: number) => (
            <Chip
              key={index}
              label={role}
              size="small"
              variant="outlined"
              color="primary"
            />
          ))}
          {params.value.length > 2 && (
            <Chip
              label={`+${params.value.length - 2}`}
              size="small"
              variant="outlined"
              color="default"
            />
          )}
        </Stack>
      ),
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params: GridRenderCellParams) => {
        const statusConfig = {
          active: { color: 'success' as const, icon: <ActiveIcon /> },
          inactive: { color: 'default' as const, icon: <InactiveIcon /> },
          pending: { color: 'warning' as const, icon: <PendingIcon /> },
          suspended: { color: 'error' as const, icon: <LockIcon /> }
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
      field: 'security',
      headerName: 'Security',
      width: 140,
      renderCell: (params: GridRenderCellParams) => (
        <Stack direction="row" spacing={0.5}>
          <Tooltip title={params.row.email_verified ? 'Email Verified' : 'Email Not Verified'}>
            <Chip
              label="Email"
              size="small"
              color={params.row.email_verified ? 'success' : 'error'}
              variant="outlined"
            />
          </Tooltip>
          <Tooltip title={params.row.two_factor_enabled ? '2FA Enabled' : '2FA Disabled'}>
            <Chip
              label="2FA"
              size="small"
              color={params.row.two_factor_enabled ? 'success' : 'warning'}
              variant="outlined"
            />
          </Tooltip>
        </Stack>
      ),
    },
    {
      field: 'last_login',
      headerName: 'Last Login',
      width: 140,
      renderCell: (params: GridRenderCellParams) => (
        <Box>
          <Typography variant="body2">
            {params.value ? new Date(params.value).toLocaleDateString() : 'Never'}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {params.row.login_count} logins
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
          label="View Details"
          onClick={() => {
            setSelectedUser(params.row);
            setUserDetailOpen(true);
          }}
          showInMenu
        />,
        <GridActionsCellItem
          icon={<EditIcon />}
          label="Edit User"
          onClick={() => navigate(`/admin/users/${params.id}/edit`)}
          showInMenu
        />,
        <GridActionsCellItem
          icon={<SecurityIcon />}
          label="Security Settings"
          onClick={() => navigate(`/admin/users/${params.id}/security`)}
          showInMenu
        />,
        <GridActionsCellItem
          icon={<EmailIcon />}
          label="Send Email"
          onClick={() => handleSendEmail(params.row)}
          showInMenu
        />,
        <GridActionsCellItem
          icon={params.row.status === 'active' ? <LockIcon /> : <UnlockIcon />}
          label={params.row.status === 'active' ? 'Suspend' : 'Activate'}
          onClick={() => handleToggleStatus(params.row)}
          showInMenu
        />,
        <GridActionsCellItem
          icon={<DeleteIcon />}
          label="Delete User"
          onClick={() => handleDeleteUser(params.row)}
          color="error"
          showInMenu
        />,
      ],
    },
  ], [navigate]);

  // Event handlers
  const handleFilterChange = (field: keyof UserFilters, value: string) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    setPaginationModel(prev => ({ ...prev, page: 0 }));
  };

  const handleClearFilters = () => {
    setFilters({
      search: '',
      status: '',
      department: '',
      role: '',
      is_admin: '',
      last_login_days: '',
      email_verified: '',
      two_factor_enabled: ''
    });
  };

  const handleSendEmail = (user: User) => {
    console.log('Sending email to:', user.email);
    // Implement email functionality
  };

  const handleToggleStatus = (user: User) => {
    console.log('Toggling status for user:', user.id);
    // Implement status toggle
  };

  const handleDeleteUser = (user: User) => {
    console.log('Deleting user:', user.id);
    // Implement delete functionality
  };

  const handleBulkAction = () => {
    if (selectedRows.length > 0 && bulkAction) {
      setBulkActionOpen(true);
    }
  };

  const confirmBulkAction = async () => {
    await bulkActionMutation.mutateAsync({
      action: bulkAction,
      userIds: selectedRows as number[]
    });
  };

  const handleExport = () => {
    console.log('Exporting users with filters:', filters);
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
        Filter Users
      </Typography>
      
      <Stack spacing={3}>
        <TextField
          label="Search"
          placeholder="Search by name, email, username..."
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
            <MenuItem value="pending">Pending</MenuItem>
            <MenuItem value="suspended">Suspended</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>Department</InputLabel>
          <Select
            value={filters.department}
            onChange={(e) => handleFilterChange('department', e.target.value)}
            label="Department"
          >
            <MenuItem value="">All Departments</MenuItem>
            <MenuItem value="Engineering">Engineering</MenuItem>
            <MenuItem value="Marketing">Marketing</MenuItem>
            <MenuItem value="Finance">Finance</MenuItem>
            <MenuItem value="HR">Human Resources</MenuItem>
            <MenuItem value="Sales">Sales</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>Admin Status</InputLabel>
          <Select
            value={filters.is_admin}
            onChange={(e) => handleFilterChange('is_admin', e.target.value)}
            label="Admin Status"
          >
            <MenuItem value="">All Users</MenuItem>
            <MenuItem value="true">Administrators Only</MenuItem>
            <MenuItem value="false">Regular Users Only</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>Email Verification</InputLabel>
          <Select
            value={filters.email_verified}
            onChange={(e) => handleFilterChange('email_verified', e.target.value)}
            label="Email Verification"
          >
            <MenuItem value="">All Users</MenuItem>
            <MenuItem value="true">Verified Only</MenuItem>
            <MenuItem value="false">Unverified Only</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>Two-Factor Auth</InputLabel>
          <Select
            value={filters.two_factor_enabled}
            onChange={(e) => handleFilterChange('two_factor_enabled', e.target.value)}
            label="Two-Factor Auth"
          >
            <MenuItem value="">All Users</MenuItem>
            <MenuItem value="true">2FA Enabled</MenuItem>
            <MenuItem value="false">2FA Disabled</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>Last Login</InputLabel>
          <Select
            value={filters.last_login_days}
            onChange={(e) => handleFilterChange('last_login_days', e.target.value)}
            label="Last Login"
          >
            <MenuItem value="">Any Time</MenuItem>
            <MenuItem value="1">Last 24 hours</MenuItem>
            <MenuItem value="7">Last 7 days</MenuItem>
            <MenuItem value="30">Last 30 days</MenuItem>
            <MenuItem value="90">Last 90 days</MenuItem>
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
          Failed to load users. Please try again.
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
              <UserIcon />
            </Avatar>
            User Management
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
              startIcon={<RoleIcon />}
              onClick={() => setRoleManagementOpen(true)}
            >
              Manage Roles
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
              onClick={() => navigate('/admin/users/new')}
              size="large"
            >
              Add User
            </Button>
          </Stack>
        </Box>

        {/* Key Metrics Dashboard */}
        <Grid container spacing={3} sx={{ mb: 2 }}>
          <Grid item xs={12} md={2}>
            <Card sx={{ bgcolor: 'primary.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                  <UserIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{userData?.summary.total_users || 0}</Typography>
                  <Typography variant="caption" color="text.secondary">Total Users</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2}>
            <Card sx={{ bgcolor: 'success.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                  <ActiveIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{userData?.summary.active_users || 0}</Typography>
                  <Typography variant="caption" color="text.secondary">Active Users</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2}>
            <Card sx={{ bgcolor: 'warning.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'warning.main', mr: 2 }}>
                  <AdminIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{userData?.summary.admin_users || 0}</Typography>
                  <Typography variant="caption" color="text.secondary">Administrators</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2}>
            <Card sx={{ bgcolor: 'info.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                  <PendingIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{userData?.summary.pending_users || 0}</Typography>
                  <Typography variant="caption" color="text.secondary">Pending</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2}>
            <Card sx={{ bgcolor: 'error.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'error.main', mr: 2 }}>
                  <SecurityIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{userData?.summary.without_2fa || 0}</Typography>
                  <Typography variant="caption" color="text.secondary">Without 2FA</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2}>
            <Card sx={{ bgcolor: 'secondary.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'secondary.main', mr: 2 }}>
                  <ActivityIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{userData?.summary.avg_login_frequency?.toFixed(0) || '0'}</Typography>
                  <Typography variant="caption" color="text.secondary">Avg Logins</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Quick Search */}
        <TextField
          placeholder="Quick search users..."
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
                  {selectedRows.length} user{selectedRows.length > 1 ? 's' : ''} selected
                </Typography>
                
                <Stack direction="row" spacing={2}>
                  <FormControl size="small" sx={{ minWidth: 150 }}>
                    <Select
                      value={bulkAction}
                      onChange={(e) => setBulkAction(e.target.value)}
                      displayEmpty
                    >
                      <MenuItem value="">Select Action</MenuItem>
                      <MenuItem value="activate">Activate Users</MenuItem>
                      <MenuItem value="deactivate">Deactivate Users</MenuItem>
                      <MenuItem value="require_password_reset">Require Password Reset</MenuItem>
                      <MenuItem value="send_email">Send Email</MenuItem>
                      <MenuItem value="export">Export Selected</MenuItem>
                    </Select>
                  </FormControl>
                  
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
                    onClick={handleBulkAction}
                    disabled={!bulkAction}
                  >
                    Execute Action
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
          rows={userData?.users || []}
          columns={columns}
          paginationModel={paginationModel}
          onPaginationModelChange={setPaginationModel}
          rowCount={userData?.total || 0}
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

      {/* User Detail Dialog */}
      <Dialog
        open={userDetailOpen}
        onClose={() => setUserDetailOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Stack direction="row" alignItems="center" spacing={2}>
            <Avatar src={selectedUser?.avatar_url} sx={{ width: 48, height: 48 }}>
              {selectedUser?.first_name?.[0]}{selectedUser?.last_name?.[0]}
            </Avatar>
            <Box>
              <Typography variant="h6">
                {selectedUser?.full_name}
                {selectedUser?.is_superuser && <SupervisorIcon color="error" sx={{ ml: 1 }} />}
                {selectedUser?.is_admin && !selectedUser?.is_superuser && <AdminIcon color="warning" sx={{ ml: 1 }} />}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {selectedUser?.email} • {selectedUser?.department}
              </Typography>
            </Box>
          </Stack>
        </DialogTitle>
        <DialogContent>
          {selectedUser && (
            <Tabs value={currentTab} onChange={(_, newValue) => setCurrentTab(newValue)}>
              <Tab icon={<ProfileIcon />} label="Profile" />
              <Tab icon={<SecurityIcon />} label="Security" />
              <Tab icon={<RoleIcon />} label="Roles & Permissions" />
              <Tab icon={<ActivityIcon />} label="Activity" />
            </Tabs>
          )}

          {/* Profile Tab */}
          {currentTab === 0 && selectedUser && (
            <Box sx={{ mt: 3 }}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardHeader title="Basic Information" />
                    <CardContent>
                      <Stack spacing={2}>
                        <Box>
                          <Typography variant="subtitle2" color="text.secondary">Full Name</Typography>
                          <Typography>{selectedUser.full_name}</Typography>
                        </Box>
                        <Box>
                          <Typography variant="subtitle2" color="text.secondary">Email</Typography>
                          <Typography>{selectedUser.email}</Typography>
                        </Box>
                        <Box>
                          <Typography variant="subtitle2" color="text.secondary">Phone</Typography>
                          <Typography>{selectedUser.phone || '—'}</Typography>
                        </Box>
                        <Box>
                          <Typography variant="subtitle2" color="text.secondary">Department</Typography>
                          <Typography>{selectedUser.department}</Typography>
                        </Box>
                        <Box>
                          <Typography variant="subtitle2" color="text.secondary">Position</Typography>
                          <Typography>{selectedUser.position}</Typography>
                        </Box>
                        <Box>
                          <Typography variant="subtitle2" color="text.secondary">Manager</Typography>
                          <Typography>{selectedUser.manager_name || '—'}</Typography>
                        </Box>
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardHeader title="Account Status" />
                    <CardContent>
                      <Stack spacing={2}>
                        <Box>
                          <Typography variant="subtitle2" color="text.secondary">Status</Typography>
                          <Chip
                            label={selectedUser.status.toUpperCase()}
                            color={selectedUser.status === 'active' ? 'success' : 'error'}
                            size="small"
                          />
                        </Box>
                        <Box>
                          <Typography variant="subtitle2" color="text.secondary">Account Type</Typography>
                          <Stack direction="row" spacing={1}>
                            {selectedUser.is_superuser && <Chip label="Super Admin" color="error" size="small" />}
                            {selectedUser.is_admin && !selectedUser.is_superuser && <Chip label="Administrator" color="warning" size="small" />}
                            {!selectedUser.is_admin && <Chip label="Regular User" color="primary" size="small" />}
                          </Stack>
                        </Box>
                        <Box>
                          <Typography variant="subtitle2" color="text.secondary">Created</Typography>
                          <Typography>{new Date(selectedUser.created_at).toLocaleString()}</Typography>
                        </Box>
                        <Box>
                          <Typography variant="subtitle2" color="text.secondary">Last Updated</Typography>
                          <Typography>{new Date(selectedUser.updated_at).toLocaleString()}</Typography>
                        </Box>
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Box>
          )}

          {/* Security Tab */}
          {currentTab === 1 && selectedUser && (
            <Box sx={{ mt: 3 }}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardHeader title="Authentication" />
                    <CardContent>
                      <Stack spacing={3}>
                        <Box>
                          <Typography variant="subtitle2" color="text.secondary">Email Verification</Typography>
                          <Chip
                            label={selectedUser.email_verified ? 'Verified' : 'Not Verified'}
                            color={selectedUser.email_verified ? 'success' : 'error'}
                            size="small"
                          />
                        </Box>
                        <Box>
                          <Typography variant="subtitle2" color="text.secondary">Two-Factor Authentication</Typography>
                          <Chip
                            label={selectedUser.two_factor_enabled ? 'Enabled' : 'Disabled'}
                            color={selectedUser.two_factor_enabled ? 'success' : 'warning'}
                            size="small"
                          />
                        </Box>
                        <Box>
                          <Typography variant="subtitle2" color="text.secondary">Password Expires</Typography>
                          <Typography>
                            {selectedUser.password_expires_at 
                              ? new Date(selectedUser.password_expires_at).toLocaleDateString()
                              : 'Never'
                            }
                          </Typography>
                        </Box>
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardHeader title="Login History" />
                    <CardContent>
                      <Stack spacing={2}>
                        <Box>
                          <Typography variant="subtitle2" color="text.secondary">Last Login</Typography>
                          <Typography>
                            {selectedUser.last_login 
                              ? new Date(selectedUser.last_login).toLocaleString()
                              : 'Never'
                            }
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="subtitle2" color="text.secondary">Total Logins</Typography>
                          <Typography>{selectedUser.login_count}</Typography>
                        </Box>
                        <Box>
                          <Typography variant="subtitle2" color="text.secondary">Last Activity</Typography>
                          <Typography>
                            {selectedUser.last_activity 
                              ? new Date(selectedUser.last_activity).toLocaleString()
                              : '—'
                            }
                          </Typography>
                        </Box>
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Box>
          )}

          {/* Roles & Permissions Tab */}
          {currentTab === 2 && selectedUser && (
            <Box sx={{ mt: 3 }}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardHeader title="Assigned Roles" />
                    <CardContent>
                      <Stack spacing={1}>
                        {selectedUser.roles.map((role, index) => (
                          <Chip
                            key={index}
                            label={role}
                            color="primary"
                            variant="outlined"
                            onDelete={() => {}}
                            deleteIcon={<DeleteIcon />}
                          />
                        ))}
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardHeader title="Permissions" />
                    <CardContent>
                      <List dense>
                        {selectedUser.permissions.map((permission, index) => (
                          <ListItem key={index}>
                            <ListItemIcon>
                              <PermissionIcon />
                            </ListItemIcon>
                            <ListItemText
                              primary={permission}
                              secondary="Active permission"
                            />
                          </ListItem>
                        ))}
                      </List>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUserDetailOpen(false)}>Close</Button>
          <Button
            variant="contained"
            startIcon={<EditIcon />}
            onClick={() => {
              navigate(`/admin/users/${selectedUser?.id}/edit`);
              setUserDetailOpen(false);
            }}
          >
            Edit User
          </Button>
        </DialogActions>
      </Dialog>

      {/* Bulk Action Confirmation Dialog */}
      <Dialog open={bulkActionOpen} onClose={() => setBulkActionOpen(false)}>
        <DialogTitle>Confirm Bulk Action</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to {bulkAction.replace('_', ' ')} {selectedRows.length} selected users?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This action will be applied to all selected users and cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBulkActionOpen(false)}>Cancel</Button>
          <Button
            onClick={confirmBulkAction}
            color="primary"
            variant="contained"
            disabled={bulkActionMutation.isPending}
          >
            {bulkActionMutation.isPending ? 'Processing...' : 'Confirm'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserManagementPage;