import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
  Grid,
  Divider,
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
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Slider,
  InputAdornment
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  Email as EmailIcon,
  Storage as DatabaseIcon,
  Cloud as BackupIcon,
  Speed as PerformanceIcon,
  Language as LocalizationIcon,
  Palette as ThemeIcon,
  VpnKey as AuthIcon,
  AdminPanelSettings as AdminIcon,
  Timeline as LogsIcon,
  MonitorHeart as HealthIcon,
  Update as UpdateIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon,
  ExpandMore as ExpandMoreIcon,
  Visibility as ViewIcon,
  VisibilityOff as HideIcon,
  Upload as UploadIcon,
  Download as DownloadIcon,
  RestartAlt as RestartIcon,
  Build as MaintenanceIcon
} from '@mui/icons-material';
import { apiClient } from '@/services/api';

interface SystemConfiguration {
  general: {
    app_name: string;
    app_description: string;
    company_name: string;
    company_logo_url: string;
    timezone: string;
    language: string;
    currency: string;
    date_format: string;
    time_format: string;
  };
  security: {
    password_min_length: number;
    password_require_uppercase: boolean;
    password_require_lowercase: boolean;
    password_require_numbers: boolean;
    password_require_symbols: boolean;
    password_expiry_days: number;
    max_login_attempts: number;
    lockout_duration_minutes: number;
    session_timeout_minutes: number;
    two_factor_required: boolean;
    ip_whitelist_enabled: boolean;
    allowed_ips: string[];
  };
  email: {
    smtp_host: string;
    smtp_port: number;
    smtp_username: string;
    smtp_password: string;
    smtp_use_tls: boolean;
    from_email: string;
    from_name: string;
    reply_to_email: string;
  };
  database: {
    backup_enabled: boolean;
    backup_frequency: string;
    backup_retention_days: number;
    backup_location: string;
    maintenance_window: string;
    query_timeout_seconds: number;
    connection_pool_size: number;
  };
  performance: {
    cache_enabled: boolean;
    cache_ttl_minutes: number;
    max_file_upload_mb: number;
    api_rate_limit_per_minute: number;
    log_level: string;
    log_retention_days: number;
    enable_compression: boolean;
  };
  notifications: {
    system_alerts_enabled: boolean;
    email_notifications_enabled: boolean;
    slack_webhook_url: string;
    notification_channels: string[];
    alert_thresholds: {
      cpu_usage: number;
      memory_usage: number;
      disk_usage: number;
      error_rate: number;
    };
  };
}

interface SystemHealth {
  overall_status: 'healthy' | 'warning' | 'critical';
  uptime_hours: number;
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  active_users: number;
  database_connections: number;
  queue_length: number;
  error_rate: number;
  response_time_ms: number;
  last_backup: string;
  services: Array<{
    name: string;
    status: 'running' | 'stopped' | 'error';
    uptime: string;
    memory_mb: number;
  }>;
}

interface SystemLog {
  id: number;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  category: string;
  message: string;
  user_id?: number;
  ip_address?: string;
  details?: Record<string, any>;
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

export const SystemSettingsPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  const [currentTab, setCurrentTab] = useState(0);
  const [configChanged, setConfigChanged] = useState(false);
  const [showPasswords, setShowPasswords] = useState(false);
  const [testEmailOpen, setTestEmailOpen] = useState(false);
  const [backupDialogOpen, setBackupDialogOpen] = useState(false);
  const [maintenanceDialogOpen, setMaintenanceDialogOpen] = useState(false);

  // Mock system configuration data
  const mockConfig: SystemConfiguration = {
    general: {
      app_name: 'ITDO ERP System',
      app_description: 'Comprehensive Enterprise Resource Planning Solution',
      company_name: 'ITDO Corporation',
      company_logo_url: '/logo.png',
      timezone: 'America/New_York',
      language: 'en',
      currency: 'USD',
      date_format: 'MM/DD/YYYY',
      time_format: '12h'
    },
    security: {
      password_min_length: 8,
      password_require_uppercase: true,
      password_require_lowercase: true,
      password_require_numbers: true,
      password_require_symbols: false,
      password_expiry_days: 90,
      max_login_attempts: 5,
      lockout_duration_minutes: 15,
      session_timeout_minutes: 60,
      two_factor_required: false,
      ip_whitelist_enabled: false,
      allowed_ips: ['192.168.1.0/24', '10.0.0.0/8']
    },
    email: {
      smtp_host: 'smtp.company.com',
      smtp_port: 587,
      smtp_username: 'noreply@company.com',
      smtp_password: '***********',
      smtp_use_tls: true,
      from_email: 'noreply@company.com',
      from_name: 'ITDO ERP System',
      reply_to_email: 'support@company.com'
    },
    database: {
      backup_enabled: true,
      backup_frequency: 'daily',
      backup_retention_days: 30,
      backup_location: '/backups/',
      maintenance_window: '02:00-04:00',
      query_timeout_seconds: 30,
      connection_pool_size: 50
    },
    performance: {
      cache_enabled: true,
      cache_ttl_minutes: 60,
      max_file_upload_mb: 100,
      api_rate_limit_per_minute: 1000,
      log_level: 'INFO',
      log_retention_days: 90,
      enable_compression: true
    },
    notifications: {
      system_alerts_enabled: true,
      email_notifications_enabled: true,
      slack_webhook_url: 'https://hooks.slack.com/services/...',
      notification_channels: ['email', 'slack'],
      alert_thresholds: {
        cpu_usage: 80,
        memory_usage: 85,
        disk_usage: 90,
        error_rate: 5
      }
    }
  };

  const mockSystemHealth: SystemHealth = {
    overall_status: 'healthy',
    uptime_hours: 72.5,
    cpu_usage: 45,
    memory_usage: 68,
    disk_usage: 42,
    active_users: 23,
    database_connections: 12,
    queue_length: 3,
    error_rate: 0.1,
    response_time_ms: 245,
    last_backup: '2024-01-20T02:30:00Z',
    services: [
      { name: 'Web Server', status: 'running', uptime: '72h 30m', memory_mb: 512 },
      { name: 'Database', status: 'running', uptime: '72h 30m', memory_mb: 1024 },
      { name: 'Cache Service', status: 'running', uptime: '72h 30m', memory_mb: 256 },
      { name: 'Queue Worker', status: 'running', uptime: '24h 15m', memory_mb: 128 },
      { name: 'Backup Service', status: 'running', uptime: '72h 30m', memory_mb: 64 }
    ]
  };

  const mockLogs: SystemLog[] = [
    {
      id: 1,
      timestamp: '2024-01-20T14:30:00Z',
      level: 'info',
      category: 'Authentication',
      message: 'User login successful',
      user_id: 123,
      ip_address: '192.168.1.100'
    },
    {
      id: 2,
      timestamp: '2024-01-20T14:25:00Z',
      level: 'warning',
      category: 'Performance',
      message: 'High CPU usage detected',
      details: { cpu_usage: 85, threshold: 80 }
    },
    {
      id: 3,
      timestamp: '2024-01-20T14:20:00Z',
      level: 'error',
      category: 'Database',
      message: 'Connection timeout',
      details: { query: 'SELECT * FROM large_table', duration_ms: 30000 }
    },
    {
      id: 4,
      timestamp: '2024-01-20T14:15:00Z',
      level: 'info',
      category: 'Backup',
      message: 'Automated backup completed successfully',
      details: { backup_size_mb: 2048, duration_minutes: 15 }
    }
  ];

  // Fetch system configuration
  const { data: config, isLoading: configLoading, refetch } = useQuery({
    queryKey: ['system-config'],
    queryFn: async (): Promise<SystemConfiguration> => {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 800));
      return mockConfig;
    },
  });

  // Fetch system health
  const { data: healthData } = useQuery({
    queryKey: ['system-health'],
    queryFn: async (): Promise<SystemHealth> => {
      await new Promise(resolve => setTimeout(resolve, 500));
      return mockSystemHealth;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch system logs
  const { data: logsData } = useQuery({
    queryKey: ['system-logs'],
    queryFn: async (): Promise<SystemLog[]> => {
      await new Promise(resolve => setTimeout(resolve, 600));
      return mockLogs;
    },
  });

  // Save configuration mutation
  const saveConfigMutation = useMutation({
    mutationFn: async (newConfig: SystemConfiguration) => {
      await new Promise(resolve => setTimeout(resolve, 1500));
      console.log('Saving configuration:', newConfig);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-config'] });
      setConfigChanged(false);
    },
  });

  // Test email mutation
  const testEmailMutation = useMutation({
    mutationFn: async (testEmail: string) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      console.log('Sending test email to:', testEmail);
    },
  });

  // Backup operations
  const backupMutation = useMutation({
    mutationFn: async (action: 'create' | 'restore') => {
      await new Promise(resolve => setTimeout(resolve, 3000));
      console.log('Backup action:', action);
    },
  });

  const handleConfigChange = (section: keyof SystemConfiguration, field: string, value: any) => {
    setConfigChanged(true);
    // Update configuration logic would go here
  };

  const handleSaveConfig = async () => {
    if (config) {
      await saveConfigMutation.mutateAsync(config);
    }
  };

  const handleTestEmail = async (testEmail: string) => {
    await testEmailMutation.mutateAsync(testEmail);
    setTestEmailOpen(false);
  };

  const handleBackup = async (action: 'create' | 'restore') => {
    await backupMutation.mutateAsync(action);
    setBackupDialogOpen(false);
  };

  const getHealthStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'warning': return 'warning';
      case 'critical': return 'error';
      default: return 'default';
    }
  };

  const getLogLevelIcon = (level: string) => {
    switch (level) {
      case 'info': return <InfoIcon color="info" />;
      case 'warning': return <WarningIcon color="warning" />;
      case 'error': return <ErrorIcon color="error" />;
      case 'critical': return <ErrorIcon color="error" />;
      default: return <InfoIcon />;
    }
  };

  return (
    <Box sx={{ maxWidth: 1400, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar sx={{ bgcolor: 'primary.main', width: 48, height: 48 }}>
              <SettingsIcon />
            </Avatar>
            System Settings & Administration
          </Typography>
          
          <Stack direction="row" spacing={2}>
            <IconButton onClick={() => refetch()} disabled={configLoading}>
              <RefreshIcon />
            </IconButton>
            
            <Button
              variant="outlined"
              startIcon={<HealthIcon />}
              color={getHealthStatusColor(healthData?.overall_status || 'healthy') as any}
            >
              System {healthData?.overall_status || 'Healthy'}
            </Button>
            
            <Button
              variant="outlined"
              startIcon={<MaintenanceIcon />}
              onClick={() => setMaintenanceDialogOpen(true)}
            >
              Maintenance
            </Button>
            
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSaveConfig}
              disabled={!configChanged || saveConfigMutation.isPending}
            >
              {saveConfigMutation.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </Stack>
        </Stack>

        {configChanged && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            You have unsaved changes. Click "Save Changes" to apply your modifications.
          </Alert>
        )}

        {/* System Health Overview */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={2}>
            <Card sx={{ bgcolor: 'primary.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                  <HealthIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{healthData?.uptime_hours?.toFixed(1) || '0.0'}h</Typography>
                  <Typography variant="caption" color="text.secondary">Uptime</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2}>
            <Card sx={{ bgcolor: 'info.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                  <PerformanceIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{healthData?.cpu_usage || 0}%</Typography>
                  <Typography variant="caption" color="text.secondary">CPU Usage</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2}>
            <Card sx={{ bgcolor: 'warning.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'warning.main', mr: 2 }}>
                  <DatabaseIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{healthData?.memory_usage || 0}%</Typography>
                  <Typography variant="caption" color="text.secondary">Memory</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2}>
            <Card sx={{ bgcolor: 'success.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                  <AdminIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{healthData?.active_users || 0}</Typography>
                  <Typography variant="caption" color="text.secondary">Active Users</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2}>
            <Card sx={{ bgcolor: 'error.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'error.main', mr: 2 }}>
                  <ErrorIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{healthData?.error_rate?.toFixed(1) || '0.0'}%</Typography>
                  <Typography variant="caption" color="text.secondary">Error Rate</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2}>
            <Card sx={{ bgcolor: 'secondary.50' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'secondary.main', mr: 2 }}>
                  <BackupIcon />
                </Avatar>
                <Box>
                  <Typography variant="body2" fontWeight="medium">
                    {healthData?.last_backup ? new Date(healthData.last_backup).toLocaleDateString() : 'Never'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">Last Backup</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Main Settings Tabs */}
      <Paper>
        <Tabs
          value={currentTab}
          onChange={(_, newValue) => setCurrentTab(newValue)}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<SettingsIcon />} label="General" />
          <Tab icon={<SecurityIcon />} label="Security" />
          <Tab icon={<EmailIcon />} label="Email" />
          <Tab icon={<DatabaseIcon />} label="Database" />
          <Tab icon={<PerformanceIcon />} label="Performance" />
          <Tab icon={<NotificationsIcon />} label="Notifications" />
          <Tab icon={<HealthIcon />} label="System Health" />
          <Tab icon={<LogsIcon />} label="System Logs" />
        </Tabs>

        {/* General Settings Tab */}
        <TabPanel value={currentTab} index={0}>
          <Box sx={{ p: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardHeader title="Application Settings" />
                  <CardContent>
                    <Stack spacing={3}>
                      <TextField
                        label="Application Name"
                        value={config?.general.app_name || ''}
                        onChange={(e) => handleConfigChange('general', 'app_name', e.target.value)}
                        fullWidth
                      />
                      <TextField
                        label="Application Description"
                        value={config?.general.app_description || ''}
                        onChange={(e) => handleConfigChange('general', 'app_description', e.target.value)}
                        multiline
                        rows={3}
                        fullWidth
                      />
                      <TextField
                        label="Company Name"
                        value={config?.general.company_name || ''}
                        onChange={(e) => handleConfigChange('general', 'company_name', e.target.value)}
                        fullWidth
                      />
                      <TextField
                        label="Company Logo URL"
                        value={config?.general.company_logo_url || ''}
                        onChange={(e) => handleConfigChange('general', 'company_logo_url', e.target.value)}
                        fullWidth
                        InputProps={{
                          endAdornment: (
                            <InputAdornment position="end">
                              <Button startIcon={<UploadIcon />} size="small">
                                Upload
                              </Button>
                            </InputAdornment>
                          )
                        }}
                      />
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardHeader title="Localization Settings" />
                  <CardContent>
                    <Stack spacing={3}>
                      <FormControl fullWidth>
                        <InputLabel>Timezone</InputLabel>
                        <Select
                          value={config?.general.timezone || ''}
                          onChange={(e) => handleConfigChange('general', 'timezone', e.target.value)}
                          label="Timezone"
                        >
                          <MenuItem value="America/New_York">Eastern (New York)</MenuItem>
                          <MenuItem value="America/Chicago">Central (Chicago)</MenuItem>
                          <MenuItem value="America/Denver">Mountain (Denver)</MenuItem>
                          <MenuItem value="America/Los_Angeles">Pacific (Los Angeles)</MenuItem>
                          <MenuItem value="UTC">UTC</MenuItem>
                        </Select>
                      </FormControl>

                      <FormControl fullWidth>
                        <InputLabel>Language</InputLabel>
                        <Select
                          value={config?.general.language || ''}
                          onChange={(e) => handleConfigChange('general', 'language', e.target.value)}
                          label="Language"
                        >
                          <MenuItem value="en">English</MenuItem>
                          <MenuItem value="es">Spanish</MenuItem>
                          <MenuItem value="fr">French</MenuItem>
                          <MenuItem value="de">German</MenuItem>
                          <MenuItem value="ja">Japanese</MenuItem>
                        </Select>
                      </FormControl>

                      <FormControl fullWidth>
                        <InputLabel>Currency</InputLabel>
                        <Select
                          value={config?.general.currency || ''}
                          onChange={(e) => handleConfigChange('general', 'currency', e.target.value)}
                          label="Currency"
                        >
                          <MenuItem value="USD">USD - US Dollar</MenuItem>
                          <MenuItem value="EUR">EUR - Euro</MenuItem>
                          <MenuItem value="GBP">GBP - British Pound</MenuItem>
                          <MenuItem value="JPY">JPY - Japanese Yen</MenuItem>
                          <MenuItem value="CAD">CAD - Canadian Dollar</MenuItem>
                        </Select>
                      </FormControl>

                      <FormControl fullWidth>
                        <InputLabel>Date Format</InputLabel>
                        <Select
                          value={config?.general.date_format || ''}
                          onChange={(e) => handleConfigChange('general', 'date_format', e.target.value)}
                          label="Date Format"
                        >
                          <MenuItem value="MM/DD/YYYY">MM/DD/YYYY</MenuItem>
                          <MenuItem value="DD/MM/YYYY">DD/MM/YYYY</MenuItem>
                          <MenuItem value="YYYY-MM-DD">YYYY-MM-DD</MenuItem>
                          <MenuItem value="DD MMM YYYY">DD MMM YYYY</MenuItem>
                        </Select>
                      </FormControl>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>

        {/* Security Settings Tab */}
        <TabPanel value={currentTab} index={1}>
          <Box sx={{ p: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardHeader title="Password Policy" />
                  <CardContent>
                    <Stack spacing={3}>
                      <TextField
                        label="Minimum Password Length"
                        type="number"
                        value={config?.security.password_min_length || 8}
                        onChange={(e) => handleConfigChange('security', 'password_min_length', parseInt(e.target.value))}
                        inputProps={{ min: 6, max: 50 }}
                        fullWidth
                      />
                      <FormControlLabel
                        control={
                          <Switch
                            checked={config?.security.password_require_uppercase || false}
                            onChange={(e) => handleConfigChange('security', 'password_require_uppercase', e.target.checked)}
                          />
                        }
                        label="Require uppercase letters"
                      />
                      <FormControlLabel
                        control={
                          <Switch
                            checked={config?.security.password_require_lowercase || false}
                            onChange={(e) => handleConfigChange('security', 'password_require_lowercase', e.target.checked)}
                          />
                        }
                        label="Require lowercase letters"
                      />
                      <FormControlLabel
                        control={
                          <Switch
                            checked={config?.security.password_require_numbers || false}
                            onChange={(e) => handleConfigChange('security', 'password_require_numbers', e.target.checked)}
                          />
                        }
                        label="Require numbers"
                      />
                      <FormControlLabel
                        control={
                          <Switch
                            checked={config?.security.password_require_symbols || false}
                            onChange={(e) => handleConfigChange('security', 'password_require_symbols', e.target.checked)}
                          />
                        }
                        label="Require special characters"
                      />
                      <TextField
                        label="Password Expiry (days)"
                        type="number"
                        value={config?.security.password_expiry_days || 90}
                        onChange={(e) => handleConfigChange('security', 'password_expiry_days', parseInt(e.target.value))}
                        inputProps={{ min: 0, max: 365 }}
                        fullWidth
                        helperText="Set to 0 for no expiry"
                      />
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardHeader title="Access Control" />
                  <CardContent>
                    <Stack spacing={3}>
                      <TextField
                        label="Max Login Attempts"
                        type="number"
                        value={config?.security.max_login_attempts || 5}
                        onChange={(e) => handleConfigChange('security', 'max_login_attempts', parseInt(e.target.value))}
                        inputProps={{ min: 1, max: 20 }}
                        fullWidth
                      />
                      <TextField
                        label="Lockout Duration (minutes)"
                        type="number"
                        value={config?.security.lockout_duration_minutes || 15}
                        onChange={(e) => handleConfigChange('security', 'lockout_duration_minutes', parseInt(e.target.value))}
                        inputProps={{ min: 1, max: 1440 }}
                        fullWidth
                      />
                      <TextField
                        label="Session Timeout (minutes)"
                        type="number"
                        value={config?.security.session_timeout_minutes || 60}
                        onChange={(e) => handleConfigChange('security', 'session_timeout_minutes', parseInt(e.target.value))}
                        inputProps={{ min: 5, max: 1440 }}
                        fullWidth
                      />
                      <FormControlLabel
                        control={
                          <Switch
                            checked={config?.security.two_factor_required || false}
                            onChange={(e) => handleConfigChange('security', 'two_factor_required', e.target.checked)}
                          />
                        }
                        label="Require Two-Factor Authentication"
                      />
                      <FormControlLabel
                        control={
                          <Switch
                            checked={config?.security.ip_whitelist_enabled || false}
                            onChange={(e) => handleConfigChange('security', 'ip_whitelist_enabled', e.target.checked)}
                          />
                        }
                        label="Enable IP Whitelist"
                      />
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>

        {/* Email Settings Tab */}
        <TabPanel value={currentTab} index={2}>
          <Box sx={{ p: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardHeader 
                    title="SMTP Configuration"
                    action={
                      <Button
                        startIcon={<EmailIcon />}
                        onClick={() => setTestEmailOpen(true)}
                      >
                        Test Email
                      </Button>
                    }
                  />
                  <CardContent>
                    <Stack spacing={3}>
                      <TextField
                        label="SMTP Host"
                        value={config?.email.smtp_host || ''}
                        onChange={(e) => handleConfigChange('email', 'smtp_host', e.target.value)}
                        fullWidth
                      />
                      <TextField
                        label="SMTP Port"
                        type="number"
                        value={config?.email.smtp_port || 587}
                        onChange={(e) => handleConfigChange('email', 'smtp_port', parseInt(e.target.value))}
                        fullWidth
                      />
                      <TextField
                        label="SMTP Username"
                        value={config?.email.smtp_username || ''}
                        onChange={(e) => handleConfigChange('email', 'smtp_username', e.target.value)}
                        fullWidth
                      />
                      <TextField
                        label="SMTP Password"
                        type={showPasswords ? 'text' : 'password'}
                        value={config?.email.smtp_password || ''}
                        onChange={(e) => handleConfigChange('email', 'smtp_password', e.target.value)}
                        fullWidth
                        InputProps={{
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton onClick={() => setShowPasswords(!showPasswords)}>
                                {showPasswords ? <VisibilityOff /> : <Visibility />}
                              </IconButton>
                            </InputAdornment>
                          )
                        }}
                      />
                      <FormControlLabel
                        control={
                          <Switch
                            checked={config?.email.smtp_use_tls || false}
                            onChange={(e) => handleConfigChange('email', 'smtp_use_tls', e.target.checked)}
                          />
                        }
                        label="Use TLS Encryption"
                      />
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardHeader title="Email Defaults" />
                  <CardContent>
                    <Stack spacing={3}>
                      <TextField
                        label="From Email"
                        value={config?.email.from_email || ''}
                        onChange={(e) => handleConfigChange('email', 'from_email', e.target.value)}
                        fullWidth
                      />
                      <TextField
                        label="From Name"
                        value={config?.email.from_name || ''}
                        onChange={(e) => handleConfigChange('email', 'from_name', e.target.value)}
                        fullWidth
                      />
                      <TextField
                        label="Reply-To Email"
                        value={config?.email.reply_to_email || ''}
                        onChange={(e) => handleConfigChange('email', 'reply_to_email', e.target.value)}
                        fullWidth
                      />
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>

        {/* System Health Tab */}
        <TabPanel value={currentTab} index={6}>
          <Box sx={{ p: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={8}>
                <Card>
                  <CardHeader title="System Services" />
                  <CardContent>
                    <TableContainer>
                      <Table>
                        <TableHead>
                          <TableRow>
                            <TableCell>Service</TableCell>
                            <TableCell>Status</TableCell>
                            <TableCell>Uptime</TableCell>
                            <TableCell>Memory Usage</TableCell>
                            <TableCell>Actions</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {healthData?.services.map((service) => (
                            <TableRow key={service.name}>
                              <TableCell>
                                <Typography variant="body2" fontWeight="medium">
                                  {service.name}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                <Chip
                                  label={service.status}
                                  size="small"
                                  color={service.status === 'running' ? 'success' : 'error'}
                                />
                              </TableCell>
                              <TableCell>{service.uptime}</TableCell>
                              <TableCell>{service.memory_mb} MB</TableCell>
                              <TableCell>
                                <IconButton size="small">
                                  <RestartIcon />
                                </IconButton>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={4}>
                <Card>
                  <CardHeader title="Performance Metrics" />
                  <CardContent>
                    <Stack spacing={3}>
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          CPU Usage: {healthData?.cpu_usage}%
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={healthData?.cpu_usage || 0}
                          color={healthData?.cpu_usage && healthData.cpu_usage > 80 ? 'error' : 'primary'}
                          sx={{ height: 8, borderRadius: 4 }}
                        />
                      </Box>
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Memory Usage: {healthData?.memory_usage}%
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={healthData?.memory_usage || 0}
                          color={healthData?.memory_usage && healthData.memory_usage > 85 ? 'warning' : 'primary'}
                          sx={{ height: 8, borderRadius: 4 }}
                        />
                      </Box>
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Disk Usage: {healthData?.disk_usage}%
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={healthData?.disk_usage || 0}
                          color={healthData?.disk_usage && healthData.disk_usage > 90 ? 'error' : 'success'}
                          sx={{ height: 8, borderRadius: 4 }}
                        />
                      </Box>
                      <Divider />
                      <Box>
                        <Typography variant="subtitle2" color="text.secondary">Response Time</Typography>
                        <Typography variant="h6">{healthData?.response_time_ms}ms</Typography>
                      </Box>
                      <Box>
                        <Typography variant="subtitle2" color="text.secondary">Queue Length</Typography>
                        <Typography variant="h6">{healthData?.queue_length}</Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>

        {/* System Logs Tab */}
        <TabPanel value={currentTab} index={7}>
          <Box sx={{ p: 3 }}>
            <Card>
              <CardHeader 
                title="Recent System Logs"
                action={
                  <Button startIcon={<DownloadIcon />}>
                    Export Logs
                  </Button>
                }
              />
              <CardContent>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Timestamp</TableCell>
                        <TableCell>Level</TableCell>
                        <TableCell>Category</TableCell>
                        <TableCell>Message</TableCell>
                        <TableCell>Details</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {logsData?.map((log) => (
                        <TableRow key={log.id}>
                          <TableCell>
                            <Typography variant="body2">
                              {new Date(log.timestamp).toLocaleString()}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Box display="flex" alignItems="center" gap={1}>
                              {getLogLevelIcon(log.level)}
                              <Typography variant="body2" textTransform="uppercase">
                                {log.level}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip label={log.category} size="small" variant="outlined" />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {log.message}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            {log.details ? (
                              <Tooltip title={JSON.stringify(log.details, null, 2)}>
                                <IconButton size="small">
                                  <ViewIcon />
                                </IconButton>
                              </Tooltip>
                            ) : (
                              '—'
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Box>
        </TabPanel>
      </Paper>

      {/* Test Email Dialog */}
      <Dialog open={testEmailOpen} onClose={() => setTestEmailOpen(false)}>
        <DialogTitle>Send Test Email</DialogTitle>
        <DialogContent>
          <TextField
            label="Test Email Address"
            type="email"
            fullWidth
            margin="normal"
            placeholder="Enter email address to test SMTP configuration"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestEmailOpen(false)}>Cancel</Button>
          <Button
            onClick={() => handleTestEmail('test@example.com')}
            variant="contained"
            disabled={testEmailMutation.isPending}
          >
            {testEmailMutation.isPending ? 'Sending...' : 'Send Test Email'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Maintenance Dialog */}
      <Dialog open={maintenanceDialogOpen} onClose={() => setMaintenanceDialogOpen(false)}>
        <DialogTitle>System Maintenance</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            Choose a maintenance operation to perform:
          </Typography>
          <Stack spacing={2} sx={{ mt: 2 }}>
            <Button
              variant="outlined"
              startIcon={<BackupIcon />}
              onClick={() => setBackupDialogOpen(true)}
              fullWidth
            >
              Create System Backup
            </Button>
            <Button
              variant="outlined"
              startIcon={<RestartIcon />}
              fullWidth
            >
              Restart Services
            </Button>
            <Button
              variant="outlined"
              startIcon={<UpdateIcon />}
              fullWidth
            >
              Check for Updates
            </Button>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMaintenanceDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SystemSettingsPage;