// @ts-nocheck
/**
 * Feature Flags Manager Component
 * Admin interface for managing feature flags
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardHeader,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  FormControlLabel,
  FormLabel,
  IconButton,
  MenuItem,
  Paper,
  Select,
  Slider,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Chip,
  Alert,
  LinearProgress,
  Tooltip,
  Grid,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  TrendingUp as TrendingUpIcon,
  Security as SecurityIcon,
  Group as GroupIcon,
  Business as BusinessIcon,
} from '@mui/icons-material';
import { featureFlagsService, FeatureFlag, CreateFeatureFlagRequest, UpdateFeatureFlagRequest } from '../../services/featureFlags';

interface FlagFormData {
  key: string;
  name: string;
  description: string;
  enabled: boolean;
  strategy: string;
  percentage: number;
  userIds: string;
  organizationIds: string;
  roles: string;
}

const STRATEGIES = [
  { value: 'all_on', label: 'All On', icon: '🟢', description: 'Always enabled for everyone' },
  { value: 'all_off', label: 'All Off', icon: '🔴', description: 'Always disabled for everyone' },
  { value: 'percentage', label: 'Percentage Rollout', icon: '📊', description: 'Enable for a percentage of users' },
  { value: 'user_list', label: 'User Whitelist', icon: '👤', description: 'Enable for specific users' },
  { value: 'user_percentage', label: 'User Percentage', icon: '👥', description: 'Enable for percentage of authenticated users' },
  { value: 'organization', label: 'Organization', icon: '🏢', description: 'Enable for specific organizations' },
  { value: 'role_based', label: 'Role Based', icon: '🔐', description: 'Enable for users with specific roles' },
  { value: 'gradual_rollout', label: 'Gradual Rollout', icon: '📈', description: 'Progressive percentage-based rollout' },
];

const FeatureFlagsManager: React.FC = () => {
  const [flags, setFlags] = useState<FeatureFlag[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [openDialog, setOpenDialog] = useState<boolean>(false);
  const [openViewDialog, setOpenViewDialog] = useState<boolean>(false);
  const [editingFlag, setEditingFlag] = useState<FeatureFlag | null>(null);
  const [viewingFlag, setViewingFlag] = useState<any>(null);
  const [formData, setFormData] = useState<FlagFormData>({
    key: '',
    name: '',
    description: '',
    enabled: false,
    strategy: 'all_off',
    percentage: 0,
    userIds: '',
    organizationIds: '',
    roles: '',
  });

  // Load feature flags
  useEffect(() => {
    loadFlags();
  }, []);

  const loadFlags = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await featureFlagsService.listFlags();
      setFlags(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load feature flags');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateFlag = () => {
    setEditingFlag(null);
    setFormData({
      key: '',
      name: '',
      description: '',
      enabled: false,
      strategy: 'all_off',
      percentage: 0,
      userIds: '',
      organizationIds: '',
      roles: '',
    });
    setOpenDialog(true);
  };

  const handleEditFlag = (flag: FeatureFlag) => {
    setEditingFlag(flag);
    setFormData({
      key: flag.key,
      name: flag.name,
      description: flag.description || '',
      enabled: flag.enabled,
      strategy: flag.strategy,
      percentage: 0, // Would need to extract from rules
      userIds: '',
      organizationIds: '',
      roles: '',
    });
    setOpenDialog(true);
  };

  const handleViewFlag = async (flag: FeatureFlag) => {
    try {
      const status = await featureFlagsService.getFlagStatus(flag.key);
      setViewingFlag(status);
      setOpenViewDialog(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load flag status');
    }
  };

  const handleDeleteFlag = async (key: string) => {
    if (window.confirm(`Are you sure you want to delete feature flag '${key}'? This action cannot be undone.`)) {
      try {
        await featureFlagsService.deleteFlag(key);
        await loadFlags();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete feature flag');
      }
    }
  };

  const handleSubmit = async () => {
    try {
      const request: CreateFeatureFlagRequest | UpdateFeatureFlagRequest = {
        name: formData.name,
        description: formData.description,
        enabled: formData.enabled,
        strategy: formData.strategy,
        ...(formData.percentage > 0 && { percentage: formData.percentage }),
        ...(formData.userIds && { userIds: formData.userIds.split(',').map(id => id.trim()) }),
        ...(formData.organizationIds && { organizationIds: formData.organizationIds.split(',').map(id => id.trim()) }),
        ...(formData.roles && { roles: formData.roles.split(',').map(role => role.trim()) }),
      };

      if (editingFlag) {
        await featureFlagsService.updateFlag(editingFlag.key, request as UpdateFeatureFlagRequest);
      } else {
        await featureFlagsService.createFlag({ key: formData.key, ...request } as CreateFeatureFlagRequest);
      }

      setOpenDialog(false);
      await loadFlags();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save feature flag');
    }
  };

  const handleToggleFlag = async (flag: FeatureFlag) => {
    try {
      await featureFlagsService.updateFlag(flag.key, { enabled: !flag.enabled });
      await loadFlags();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle feature flag');
    }
  };

  const getStrategyInfo = (strategy: string) => {
    return STRATEGIES.find(s => s.value === strategy) || STRATEGIES[0];
  };

  const handleFormChange = (field: keyof FlagFormData) => (event: any) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value;
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  if (loading && flags.length === 0) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2 }}>Loading feature flags...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          🎛️ Feature Flags Manager
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreateFlag}
          color="primary"
        >
          Create Flag
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Card>
        <CardHeader title="Feature Flags" />
        <CardContent>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Key</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Strategy</TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {flags.map((flag) => {
                  const strategyInfo = getStrategyInfo(flag.strategy);
                  return (
                    <TableRow key={flag.key}>
                      <TableCell>
                        <Typography variant="subtitle2">{flag.name}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                          {flag.key}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={flag.enabled ? 'Enabled' : 'Disabled'}
                          color={flag.enabled ? 'success' : 'default'}
                          size="small"
                          onClick={() => handleToggleFlag(flag)}
                          clickable
                        />
                      </TableCell>
                      <TableCell>
                        <Tooltip title={strategyInfo.description}>
                          <Chip
                            label={`${strategyInfo.icon} ${strategyInfo.label}`}
                            variant="outlined"
                            size="small"
                          />
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {flag.description || 'No description'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Tooltip title="View Details">
                            <IconButton size="small" onClick={() => handleViewFlag(flag)}>
                              <ViewIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Edit">
                            <IconButton size="small" onClick={() => handleEditFlag(flag)}>
                              <EditIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete">
                            <IconButton
                              size="small"
                              onClick={() => handleDeleteFlag(flag.key)}
                              color="error"
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  );
                })}
                {flags.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      <Typography color="text.secondary">
                        No feature flags configured. Create your first flag to get started.
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Create/Edit Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingFlag ? `Edit Feature Flag: ${editingFlag.key}` : 'Create New Feature Flag'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Flag Key"
                value={formData.key}
                onChange={handleFormChange('key')}
                disabled={!!editingFlag}
                helperText="Unique identifier (cannot be changed after creation)"
                sx={{ mb: 2 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Display Name"
                value={formData.name}
                onChange={handleFormChange('name')}
                sx={{ mb: 2 }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={handleFormChange('description')}
                multiline
                rows={2}
                sx={{ mb: 2 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.enabled}
                    onChange={handleFormChange('enabled')}
                  />
                }
                label="Enabled"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <FormLabel>Strategy</FormLabel>
                <Select
                  value={formData.strategy}
                  onChange={handleFormChange('strategy')}
                >
                  {STRATEGIES.map((strategy) => (
                    <MenuItem key={strategy.value} value={strategy.value}>
                      {strategy.icon} {strategy.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            {/* Strategy-specific fields */}
            {(formData.strategy === 'percentage' || formData.strategy === 'gradual_rollout') && (
              <Grid item xs={12}>
                <FormLabel>Rollout Percentage: {formData.percentage}%</FormLabel>
                <Slider
                  value={formData.percentage}
                  onChange={(_, value) => setFormData(prev => ({ ...prev, percentage: value as number }))}
                  valueLabelDisplay="auto"
                  step={1}
                  marks
                  min={0}
                  max={100}
                  sx={{ mt: 2, mb: 2 }}
                />
              </Grid>
            )}
            
            {formData.strategy === 'user_list' && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="User IDs"
                  value={formData.userIds}
                  onChange={handleFormChange('userIds')}
                  helperText="Comma-separated list of user IDs"
                  placeholder="user1, user2, user3"
                  sx={{ mb: 2 }}
                />
              </Grid>
            )}
            
            {formData.strategy === 'organization' && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Organization IDs"
                  value={formData.organizationIds}
                  onChange={handleFormChange('organizationIds')}
                  helperText="Comma-separated list of organization IDs"
                  placeholder="org1, org2, org3"
                  sx={{ mb: 2 }}
                />
              </Grid>
            )}
            
            {formData.strategy === 'role_based' && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Required Roles"
                  value={formData.roles}
                  onChange={handleFormChange('roles')}
                  helperText="Comma-separated list of required roles"
                  placeholder="admin, premium_user, beta_tester"
                  sx={{ mb: 2 }}
                />
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingFlag ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Details Dialog */}
      <Dialog open={openViewDialog} onClose={() => setOpenViewDialog(false)} maxWidth="lg" fullWidth>
        <DialogTitle>Feature Flag Details</DialogTitle>
        <DialogContent>
          {viewingFlag && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardHeader title="Configuration" />
                  <CardContent>
                    <Typography variant="body2" gutterBottom>
                      <strong>Key:</strong> {viewingFlag.config?.key}
                    </Typography>
                    <Typography variant="body2" gutterBottom>
                      <strong>Strategy:</strong> {viewingFlag.config?.strategy}
                    </Typography>
                    <Typography variant="body2" gutterBottom>
                      <strong>Enabled:</strong> {viewingFlag.config?.enabled ? 'Yes' : 'No'}
                    </Typography>
                    <Typography variant="body2" gutterBottom>
                      <strong>Last Updated:</strong> {viewingFlag.config?.updated_at}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardHeader title="Statistics" />
                  <CardContent>
                    <Typography variant="body2" gutterBottom>
                      <strong>Total Evaluations:</strong> {viewingFlag.statistics?.total_evaluations || 0}
                    </Typography>
                    <Typography variant="body2" gutterBottom>
                      <strong>Enabled Count:</strong> {viewingFlag.statistics?.enabled_count || 0}
                    </Typography>
                    <Typography variant="body2" gutterBottom>
                      <strong>Enabled Percentage:</strong> {viewingFlag.statistics?.enabled_percentage?.toFixed(1) || 0}%
                    </Typography>
                    <Typography variant="body2" gutterBottom>
                      <strong>Last Evaluated:</strong> {viewingFlag.last_evaluated || 'Never'}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenViewDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FeatureFlagsManager;
