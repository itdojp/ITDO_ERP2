import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  LinearProgress,
  Tabs,
  Tab,
  Avatar,
  Divider,
  TreeView,
  TreeItem,
  Autocomplete
} from '@mui/material';
import {
  Warehouse as WarehouseIcon,
  LocationOn as LocationIcon,
  QrCodeScanner as QrIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  MoveToInbox as MoveIcon,
  Assignment as TransferIcon,
  Map as MapIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  ExpandMore as ExpandMoreIcon,
  ChevronRight as ChevronRightIcon,
  Inventory as InventoryIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  Room as BinIcon,
  LocalShipping as ShippingIcon,
  AccountTree as HierarchyIcon
} from '@mui/icons-material';
import { apiClient } from '@/services/api';

interface Warehouse {
  id: number;
  code: string;
  name: string;
  description?: string;
  address?: string;
  manager?: string;
  phone?: string;
  email?: string;
  is_active: boolean;
  total_locations: number;
  occupied_locations: number;
  total_capacity: number;
  used_capacity: number;
  total_items: number;
  total_value: number;
  created_at: string;
  updated_at: string;
}

interface WarehouseLocation {
  id: number;
  warehouse_id: number;
  zone: string;
  aisle: string;
  rack: string;
  shelf: string;
  bin: string;
  full_location: string;
  location_type: 'storage' | 'receiving' | 'shipping' | 'quality_control' | 'staging';
  capacity: number;
  current_usage: number;
  is_occupied: boolean;
  is_reserved: boolean;
  product_id?: number;
  product_name?: string;
  product_code?: string;
  quantity?: number;
  last_movement_date?: string;
  temperature_controlled?: boolean;
  hazmat_approved?: boolean;
  weight_limit?: number;
}

interface LocationMovement {
  id: number;
  product_id: number;
  product_code: string;
  product_name: string;
  from_location?: string;
  to_location: string;
  quantity: number;
  movement_type: 'receive' | 'ship' | 'transfer' | 'cycle_count' | 'adjustment';
  reference: string;
  operator: string;
  timestamp: string;
  notes?: string;
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

export const WarehouseManagementPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  const [currentTab, setCurrentTab] = useState(0);
  const [selectedWarehouse, setSelectedWarehouse] = useState<number | null>(null);
  const [locationDialogOpen, setLocationDialogOpen] = useState(false);
  const [transferDialogOpen, setTransferDialogOpen] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState<WarehouseLocation | null>(null);
  const [transferData, setTransferData] = useState({
    product_id: '',
    from_location: '',
    to_location: '',
    quantity: '',
    notes: ''
  });

  // Fetch warehouses
  const { data: warehouses, isLoading: warehousesLoading } = useQuery({
    queryKey: ['warehouses'],
    queryFn: async (): Promise<Warehouse[]> => {
      const response = await apiClient.get('/api/v1/warehouses');
      return response.data || [];
    },
  });

  // Fetch warehouse locations
  const { data: locations, isLoading: locationsLoading } = useQuery({
    queryKey: ['warehouse-locations', selectedWarehouse],
    queryFn: async (): Promise<WarehouseLocation[]> => {
      if (!selectedWarehouse) return [];
      const response = await apiClient.get(`/api/v1/warehouses/${selectedWarehouse}/locations`);
      return response.data || [];
    },
    enabled: !!selectedWarehouse,
  });

  // Fetch location movements
  const { data: movements } = useQuery({
    queryKey: ['location-movements', selectedWarehouse],
    queryFn: async (): Promise<LocationMovement[]> => {
      if (!selectedWarehouse) return [];
      const response = await apiClient.get(`/api/v1/warehouses/${selectedWarehouse}/movements`);
      return response.data || [];
    },
    enabled: !!selectedWarehouse,
  });

  // Location transfer mutation
  const transferMutation = useMutation({
    mutationFn: async (transfer: any) => {
      await apiClient.post('/api/v1/warehouses/transfer', transfer);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['warehouse-locations'] });
      queryClient.invalidateQueries({ queryKey: ['location-movements'] });
      setTransferDialogOpen(false);
      setTransferData({
        product_id: '',
        from_location: '',
        to_location: '',
        quantity: '',
        notes: ''
      });
    },
  });

  // Location creation mutation
  const createLocationMutation = useMutation({
    mutationFn: async (location: Partial<WarehouseLocation>) => {
      await apiClient.post(`/api/v1/warehouses/${selectedWarehouse}/locations`, location);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['warehouse-locations'] });
      setLocationDialogOpen(false);
    },
  });

  const handleTransfer = async () => {
    if (transferData.product_id && transferData.from_location && transferData.to_location && transferData.quantity) {
      await transferMutation.mutateAsync({
        ...transferData,
        warehouse_id: selectedWarehouse,
        quantity: parseFloat(transferData.quantity)
      });
    }
  };

  const selectedWarehouseData = warehouses?.find(w => w.id === selectedWarehouse);

  // Generate location hierarchy for TreeView
  const locationHierarchy = useMemo(() => {
    if (!locations) return {};
    
    const hierarchy: any = {};
    locations.forEach(location => {
      if (!hierarchy[location.zone]) {
        hierarchy[location.zone] = {};
      }
      if (!hierarchy[location.zone][location.aisle]) {
        hierarchy[location.zone][location.aisle] = {};
      }
      if (!hierarchy[location.zone][location.aisle][location.rack]) {
        hierarchy[location.zone][location.aisle][location.rack] = {};
      }
      if (!hierarchy[location.zone][location.aisle][location.rack][location.shelf]) {
        hierarchy[location.zone][location.aisle][location.rack][location.shelf] = [];
      }
      hierarchy[location.zone][location.aisle][location.rack][location.shelf].push(location);
    });
    
    return hierarchy;
  }, [locations]);

  const renderLocationTree = (hierarchy: any) => {
    return Object.entries(hierarchy).map(([zone, aisles]: [string, any]) => (
      <TreeItem key={zone} nodeId={zone} label={`Zone: ${zone}`}>
        {Object.entries(aisles).map(([aisle, racks]: [string, any]) => (
          <TreeItem key={`${zone}-${aisle}`} nodeId={`${zone}-${aisle}`} label={`Aisle: ${aisle}`}>
            {Object.entries(racks).map(([rack, shelves]: [string, any]) => (
              <TreeItem key={`${zone}-${aisle}-${rack}`} nodeId={`${zone}-${aisle}-${rack}`} label={`Rack: ${rack}`}>
                {Object.entries(shelves).map(([shelf, bins]: [string, any]) => (
                  <TreeItem key={`${zone}-${aisle}-${rack}-${shelf}`} nodeId={`${zone}-${aisle}-${rack}-${shelf}`} label={`Shelf: ${shelf}`}>
                    {bins.map((location: WarehouseLocation) => (
                      <TreeItem
                        key={location.id}
                        nodeId={location.id.toString()}
                        label={
                          <Box display="flex" alignItems="center" justifyContent="space-between">
                            <Typography variant="body2">
                              Bin: {location.bin}
                              {location.is_occupied && (
                                <Chip label="Occupied" size="small" color="warning" sx={{ ml: 1 }} />
                              )}
                            </Typography>
                            {location.product_name && (
                              <Typography variant="caption" color="text.secondary">
                                {location.product_name} ({location.quantity})
                              </Typography>
                            )}
                          </Box>
                        }
                      />
                    ))}
                  </TreeItem>
                ))}
              </TreeItem>
            ))}
          </TreeItem>
        ))}
      </TreeItem>
    ));
  };

  return (
    <Box sx={{ maxWidth: 1400, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h4" component="h1">
            Warehouse Management
          </Typography>
          
          <Stack direction="row" spacing={2}>
            <Button
              variant="outlined"
              startIcon={<QrIcon />}
              onClick={() => navigate('/warehouse/scan')}
            >
              QR Scanner
            </Button>
            <Button
              variant="outlined"
              startIcon={<MapIcon />}
              onClick={() => navigate('/warehouse/map')}
            >
              Warehouse Map
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setLocationDialogOpen(true)}
            >
              Add Location
            </Button>
          </Stack>
        </Stack>

        {/* Warehouse Selector */}
        <Grid container spacing={3}>
          {warehouses?.map((warehouse) => (
            <Grid item xs={12} md={6} lg={4} key={warehouse.id}>
              <Card
                sx={{
                  cursor: 'pointer',
                  border: selectedWarehouse === warehouse.id ? 2 : 1,
                  borderColor: selectedWarehouse === warehouse.id ? 'primary.main' : 'divider',
                  '&:hover': { bgcolor: 'action.hover' }
                }}
                onClick={() => setSelectedWarehouse(warehouse.id)}
              >
                <CardContent>
                  <Stack direction="row" alignItems="center" spacing={2} mb={2}>
                    <Avatar sx={{ bgcolor: 'primary.main' }}>
                      <WarehouseIcon />
                    </Avatar>
                    <Box>
                      <Typography variant="h6">{warehouse.name}</Typography>
                      <Typography variant="body2" color="text.secondary">{warehouse.code}</Typography>
                    </Box>
                    <Chip
                      label={warehouse.is_active ? 'Active' : 'Inactive'}
                      color={warehouse.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </Stack>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Locations</Typography>
                      <Typography variant="h6">{warehouse.occupied_locations}/{warehouse.total_locations}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Items</Typography>
                      <Typography variant="h6">{warehouse.total_items}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Capacity</Typography>
                      <Typography variant="body2">
                        {((warehouse.used_capacity / warehouse.total_capacity) * 100).toFixed(1)}%
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Value</Typography>
                      <Typography variant="body2">${warehouse.total_value.toFixed(0)}</Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {selectedWarehouse && selectedWarehouseData && (
        <>
          {/* Selected Warehouse Details */}
          <Paper sx={{ p: 3, mb: 3 }}>
            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h5">{selectedWarehouseData.name} - Details</Typography>
              <Stack direction="row" spacing={2}>
                <Button
                  variant="outlined"
                  startIcon={<TransferIcon />}
                  onClick={() => setTransferDialogOpen(true)}
                >
                  Transfer Stock
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<EditIcon />}
                >
                  Edit Warehouse
                </Button>
              </Stack>
            </Stack>

            <Grid container spacing={3}>
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Avatar sx={{ bgcolor: 'success.main', mx: 'auto', mb: 1 }}>
                      <LocationIcon />
                    </Avatar>
                    <Typography variant="h4">{selectedWarehouseData.occupied_locations}</Typography>
                    <Typography variant="body2" color="text.secondary">Occupied Locations</Typography>
                    <Typography variant="caption">
                      of {selectedWarehouseData.total_locations} total
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Avatar sx={{ bgcolor: 'info.main', mx: 'auto', mb: 1 }}>
                      <InventoryIcon />
                    </Avatar>
                    <Typography variant="h4">{selectedWarehouseData.total_items}</Typography>
                    <Typography variant="body2" color="text.secondary">Total Items</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Avatar sx={{ bgcolor: 'warning.main', mx: 'auto', mb: 1 }}>
                      <TrendingUpIcon />
                    </Avatar>
                    <Typography variant="h4">
                      {((selectedWarehouseData.used_capacity / selectedWarehouseData.total_capacity) * 100).toFixed(1)}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">Capacity Used</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Avatar sx={{ bgcolor: 'primary.main', mx: 'auto', mb: 1 }}>
                      <ShippingIcon />
                    </Avatar>
                    <Typography variant="h4">${selectedWarehouseData.total_value.toFixed(0)}</Typography>
                    <Typography variant="body2" color="text.secondary">Total Value</Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Paper>

          {/* Tabs */}
          <Paper sx={{ mb: 3 }}>
            <Tabs
              value={currentTab}
              onChange={(_, newValue) => setCurrentTab(newValue)}
              variant="scrollable"
              scrollButtons="auto"
            >
              <Tab icon={<HierarchyIcon />} label="Location Hierarchy" />
              <Tab icon={<LocationIcon />} label="Location Grid" />
              <Tab icon={<MoveIcon />} label="Movement History" />
              <Tab icon={<MapIcon />} label="Warehouse Layout" />
            </Tabs>
          </Paper>

          {/* Location Hierarchy Tab */}
          <TabPanel value={currentTab} index={0}>
            <Card>
              <CardHeader title="Location Hierarchy" />
              <CardContent>
                {locationsLoading ? (
                  <LinearProgress />
                ) : (
                  <TreeView
                    defaultCollapseIcon={<ExpandMoreIcon />}
                    defaultExpandIcon={<ChevronRightIcon />}
                    sx={{ flexGrow: 1, maxWidth: 400, overflowY: 'auto' }}
                  >
                    {renderLocationTree(locationHierarchy)}
                  </TreeView>
                )}
              </CardContent>
            </Card>
          </TabPanel>

          {/* Location Grid Tab */}
          <TabPanel value={currentTab} index={1}>
            <Card>
              <CardHeader 
                title="All Locations"
                action={
                  <Stack direction="row" spacing={2}>
                    <TextField
                      size="small"
                      placeholder="Search locations..."
                      InputProps={{
                        startAdornment: <SearchIcon sx={{ color: 'text.secondary', mr: 1 }} />
                      }}
                    />
                    <IconButton>
                      <FilterIcon />
                    </IconButton>
                  </Stack>
                }
              />
              <CardContent>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Location</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Product</TableCell>
                        <TableCell align="right">Quantity</TableCell>
                        <TableCell align="right">Capacity</TableCell>
                        <TableCell>Last Movement</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {locations?.map((location) => (
                        <TableRow key={location.id}>
                          <TableCell>
                            <Typography variant="body2" fontFamily="monospace">
                              {location.full_location}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip label={location.location_type} size="small" variant="outlined" />
                          </TableCell>
                          <TableCell>
                            <Stack direction="row" spacing={1}>
                              {location.is_occupied && (
                                <Chip label="Occupied" size="small" color="warning" />
                              )}
                              {location.is_reserved && (
                                <Chip label="Reserved" size="small" color="info" />
                              )}
                              {!location.is_occupied && !location.is_reserved && (
                                <Chip label="Available" size="small" color="success" />
                              )}
                            </Stack>
                          </TableCell>
                          <TableCell>
                            {location.product_name ? (
                              <Box>
                                <Typography variant="body2">{location.product_name}</Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {location.product_code}
                                </Typography>
                              </Box>
                            ) : (
                              '—'
                            )}
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" fontWeight="medium">
                              {location.quantity || 0}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2">
                              {location.current_usage}/{location.capacity}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="caption">
                              {location.last_movement_date ? 
                                new Date(location.last_movement_date).toLocaleDateString() : 
                                '—'
                              }
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Stack direction="row" spacing={1}>
                              <IconButton size="small">
                                <ViewIcon />
                              </IconButton>
                              <IconButton size="small">
                                <EditIcon />
                              </IconButton>
                              <IconButton size="small">
                                <QrIcon />
                              </IconButton>
                            </Stack>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </TabPanel>

          {/* Movement History Tab */}
          <TabPanel value={currentTab} index={2}>
            <Card>
              <CardHeader title="Recent Movements" />
              <CardContent>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Date/Time</TableCell>
                        <TableCell>Product</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>From</TableCell>
                        <TableCell>To</TableCell>
                        <TableCell align="right">Quantity</TableCell>
                        <TableCell>Operator</TableCell>
                        <TableCell>Reference</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {movements?.map((movement) => (
                        <TableRow key={movement.id}>
                          <TableCell>
                            <Typography variant="body2">
                              {new Date(movement.timestamp).toLocaleString()}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Box>
                              <Typography variant="body2">{movement.product_name}</Typography>
                              <Typography variant="caption" color="text.secondary">
                                {movement.product_code}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={movement.movement_type}
                              size="small"
                              color={
                                movement.movement_type === 'receive' ? 'success' :
                                movement.movement_type === 'ship' ? 'error' :
                                'info'
                              }
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" fontFamily="monospace">
                              {movement.from_location || '—'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" fontFamily="monospace">
                              {movement.to_location}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" fontWeight="medium">
                              {movement.quantity}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">{movement.operator}</Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">{movement.reference}</Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </TabPanel>

          {/* Warehouse Layout Tab */}
          <TabPanel value={currentTab} index={3}>
            <Card>
              <CardHeader title="Warehouse Layout" />
              <CardContent>
                <Alert severity="info">
                  Interactive warehouse map coming soon. This will show a visual representation of the warehouse layout with real-time location status.
                </Alert>
                <Box sx={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'grey.50', mt: 2 }}>
                  <Typography variant="h6" color="text.secondary">
                    Warehouse Map Placeholder
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </TabPanel>
        </>
      )}

      {/* Transfer Dialog */}
      <Dialog open={transferDialogOpen} onClose={() => setTransferDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Transfer Stock</DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <Autocomplete
              options={locations?.filter(l => l.is_occupied) || []}
              getOptionLabel={(option) => `${option.full_location} - ${option.product_name} (${option.quantity})`}
              renderInput={(params) => (
                <TextField {...params} label="From Location" fullWidth />
              )}
              onChange={(_, value) => {
                setTransferData(prev => ({
                  ...prev,
                  from_location: value?.full_location || '',
                  product_id: value?.product_id?.toString() || ''
                }));
              }}
            />
            
            <Autocomplete
              options={locations?.filter(l => !l.is_occupied) || []}
              getOptionLabel={(option) => option.full_location}
              renderInput={(params) => (
                <TextField {...params} label="To Location" fullWidth />
              )}
              onChange={(_, value) => {
                setTransferData(prev => ({
                  ...prev,
                  to_location: value?.full_location || ''
                }));
              }}
            />
            
            <TextField
              label="Quantity"
              type="number"
              fullWidth
              value={transferData.quantity}
              onChange={(e) => setTransferData(prev => ({ ...prev, quantity: e.target.value }))}
            />
            
            <TextField
              label="Notes (optional)"
              fullWidth
              multiline
              rows={3}
              value={transferData.notes}
              onChange={(e) => setTransferData(prev => ({ ...prev, notes: e.target.value }))}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTransferDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleTransfer}
            variant="contained"
            disabled={
              transferMutation.isPending ||
              !transferData.product_id ||
              !transferData.from_location ||
              !transferData.to_location ||
              !transferData.quantity
            }
          >
            {transferMutation.isPending ? 'Transferring...' : 'Transfer'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Location Dialog */}
      <Dialog open={locationDialogOpen} onClose={() => setLocationDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add New Location</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" paragraph>
            Create a new storage location in the selected warehouse.
          </Typography>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={6}>
              <TextField label="Zone" fullWidth />
            </Grid>
            <Grid item xs={6}>
              <TextField label="Aisle" fullWidth />
            </Grid>
            <Grid item xs={6}>
              <TextField label="Rack" fullWidth />
            </Grid>
            <Grid item xs={6}>
              <TextField label="Shelf" fullWidth />
            </Grid>
            <Grid item xs={6}>
              <TextField label="Bin" fullWidth />
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Type</InputLabel>
                <Select label="Type">
                  <MenuItem value="storage">Storage</MenuItem>
                  <MenuItem value="receiving">Receiving</MenuItem>
                  <MenuItem value="shipping">Shipping</MenuItem>
                  <MenuItem value="quality_control">Quality Control</MenuItem>
                  <MenuItem value="staging">Staging</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField label="Capacity" type="number" fullWidth />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLocationDialogOpen(false)}>Cancel</Button>
          <Button variant="contained">Create Location</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default WarehouseManagementPage;