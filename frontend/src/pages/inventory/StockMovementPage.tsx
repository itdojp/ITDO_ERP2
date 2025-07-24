import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  CardHeader,
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
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
  Alert,
  LinearProgress,
  IconButton,
  Avatar,
  Tabs,
  Tab,
  Autocomplete,
  Divider,
  Badge,
  Stepper,
  Step,
  StepLabel
} from '@mui/material';
import {
  QrCodeScanner as QrIcon,
  Add as AddIcon,
  Remove as RemoveIcon,
  MoveToInbox as ReceiveIcon,
  LocalShipping as ShipIcon,
  SwapHoriz as TransferIcon,
  Assignment as AdjustIcon,
  Search as SearchIcon,
  Camera as CameraIcon,
  CheckCircle as CompleteIcon,
  Pending as PendingIcon,
  Error as ErrorIcon,
  Inventory as InventoryIcon,
  LocationOn as LocationIcon,
  Person as PersonIcon,
  CalendarToday as DateIcon,
  Receipt as ReceiptIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { apiClient } from '@/services/api';

interface StockMovement {
  id: number;
  product_id: number;
  product_code: string;
  product_name: string;
  movement_type: 'receive' | 'ship' | 'transfer' | 'adjustment' | 'cycle_count';
  quantity: number;
  from_location?: string;
  to_location?: string;
  reference_number: string;
  operator: string;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  timestamp: string;
  completed_at?: string;
  notes?: string;
  attachments?: string[];
  unit_cost?: number;
  total_cost?: number;
  supplier?: string;
  customer?: string;
  reason_code?: string;
}

interface PendingMovement {
  id: number;
  product_id: number;
  product_code: string;
  product_name: string;
  movement_type: string;
  expected_quantity: number;
  scanned_quantity: number;
  location: string;
  operator: string;
  status: 'pending' | 'partial' | 'completed';
  created_at: string;
}

interface QRScanResult {
  type: 'product' | 'location' | 'batch';
  data: {
    product_id?: number;
    product_code?: string;
    location?: string;
    batch_number?: string;
    expiry_date?: string;
  };
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

export const StockMovementPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  const [currentTab, setCurrentTab] = useState(0);
  const [qrScannerOpen, setQrScannerOpen] = useState(false);
  const [movementDialogOpen, setMovementDialogOpen] = useState(false);
  const [scanStream, setScanStream] = useState<MediaStream | null>(null);
  
  const [newMovement, setNewMovement] = useState({
    product_id: '',
    movement_type: 'receive',
    quantity: '',
    location: '',
    reference: '',
    notes: '',
    supplier: '',
    unit_cost: ''
  });

  const [batchMovement, setBatchMovement] = useState({
    movement_type: 'receive',
    location: '',
    reference: '',
    operator: '',
    items: [] as any[]
  });

  const [currentStep, setCurrentStep] = useState(0);
  const movementSteps = ['Scan Items', 'Verify Quantities', 'Confirm Location', 'Complete'];

  // Fetch stock movements
  const { data: movements, isLoading: movementsLoading } = useQuery({
    queryKey: ['stock-movements'],
    queryFn: async (): Promise<StockMovement[]> => {
      const response = await apiClient.get('/api/v1/stock-movements');
      return response.data || [];
    },
    refetchInterval: 5000, // Refresh every 5 seconds for real-time updates
  });

  // Fetch pending movements
  const { data: pendingMovements } = useQuery({
    queryKey: ['pending-movements'],
    queryFn: async (): Promise<PendingMovement[]> => {
      const response = await apiClient.get('/api/v1/stock-movements/pending');
      return response.data || [];
    },
    refetchInterval: 3000,
  });

  // Fetch products for autocomplete
  const { data: products } = useQuery({
    queryKey: ['products-basic'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/products-basic');
      return response.data || [];
    },
  });

  // Fetch locations for autocomplete
  const { data: locations } = useQuery({
    queryKey: ['warehouse-locations-all'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/warehouses/locations');
      return response.data || [];
    },
  });

  // Create movement mutation
  const createMovementMutation = useMutation({
    mutationFn: async (movement: any) => {
      const response = await apiClient.post('/api/v1/stock-movements', movement);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stock-movements'] });
      queryClient.invalidateQueries({ queryKey: ['inventory-list'] });
      setMovementDialogOpen(false);
      setNewMovement({
        product_id: '',
        movement_type: 'receive',
        quantity: '',
        location: '',
        reference: '',
        notes: '',
        supplier: '',
        unit_cost: ''
      });
    },
  });

  // Complete movement mutation
  const completeMovementMutation = useMutation({
    mutationFn: async (movementId: number) => {
      await apiClient.post(`/api/v1/stock-movements/${movementId}/complete`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stock-movements'] });
      queryClient.invalidateQueries({ queryKey: ['pending-movements'] });
    },
  });

  // QR Scanner functions
  const startQRScanner = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }
      });
      setScanStream(stream);
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setQrScannerOpen(true);
    } catch (error) {
      console.error('Error starting camera:', error);
    }
  };

  const stopQRScanner = () => {
    if (scanStream) {
      scanStream.getTracks().forEach(track => track.stop());
      setScanStream(null);
    }
    setQrScannerOpen(false);
  };

  const captureQRCode = () => {
    if (videoRef.current && canvasRef.current) {
      const canvas = canvasRef.current;
      const video = videoRef.current;
      const context = canvas.getContext('2d');
      
      if (context) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0);
        
        // In a real implementation, you would use a QR code library here
        // For now, we'll simulate a scan result
        const mockScanResult: QRScanResult = {
          type: 'product',
          data: {
            product_id: 1,
            product_code: 'PROD001'
          }
        };
        
        handleQRScanResult(mockScanResult);
      }
    }
  };

  const handleQRScanResult = (result: QRScanResult) => {
    console.log('QR Scan Result:', result);
    
    if (result.type === 'product' && result.data.product_id) {
      setNewMovement(prev => ({
        ...prev,
        product_id: result.data.product_id!.toString()
      }));
    } else if (result.type === 'location' && result.data.location) {
      setNewMovement(prev => ({
        ...prev,
        location: result.data.location!
      }));
    }
    
    stopQRScanner();
  };

  const handleSubmitMovement = async () => {
    if (newMovement.product_id && newMovement.quantity && newMovement.location) {
      await createMovementMutation.mutateAsync({
        ...newMovement,
        product_id: parseInt(newMovement.product_id),
        quantity: parseFloat(newMovement.quantity),
        unit_cost: newMovement.unit_cost ? parseFloat(newMovement.unit_cost) : undefined
      });
    }
  };

  const getMovementTypeIcon = (type: string) => {
    switch (type) {
      case 'receive': return <ReceiveIcon />;
      case 'ship': return <ShipIcon />;
      case 'transfer': return <TransferIcon />;
      case 'adjustment': return <AdjustIcon />;
      default: return <InventoryIcon />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'in_progress': return 'warning';
      case 'pending': return 'info';
      case 'cancelled': return 'error';
      default: return 'default';
    }
  };

  // Cleanup camera stream on unmount
  useEffect(() => {
    return () => {
      if (scanStream) {
        scanStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [scanStream]);

  return (
    <Box sx={{ maxWidth: 1400, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h4" component="h1">
            Stock Movement
          </Typography>
          
          <Stack direction="row" spacing={2}>
            <Button
              variant="outlined"
              startIcon={<QrIcon />}
              onClick={startQRScanner}
            >
              QR Scanner
            </Button>
            <Button
              variant="outlined"
              startIcon={<SearchIcon />}
              onClick={() => navigate('/inventory/search')}
            >
              Search Products
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setMovementDialogOpen(true)}
            >
              New Movement
            </Button>
          </Stack>
        </Stack>

        {/* Quick Stats */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'warning.main', mr: 2 }}>
                  <PendingIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{pendingMovements?.length || 0}</Typography>
                  <Typography variant="caption" color="text.secondary">Pending</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                  <CompleteIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    {movements?.filter(m => m.status === 'completed').length || 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">Completed Today</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                  <ReceiveIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    {movements?.filter(m => m.movement_type === 'receive').length || 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">Received</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent sx={{ display: 'flex', alignItems: 'center', py: 2 }}>
                <Avatar sx={{ bgcolor: 'error.main', mr: 2 }}>
                  <ShipIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    {movements?.filter(m => m.movement_type === 'ship').length || 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">Shipped</Typography>
                </Box>
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
          <Tab 
            icon={<Badge badgeContent={pendingMovements?.length} color="warning"><PendingIcon /></Badge>} 
            label="Pending" 
          />
          <Tab icon={<InventoryIcon />} label="All Movements" />
          <Tab icon={<QrIcon />} label="Batch Processing" />
          <Tab icon={<ReceiptIcon />} label="Movement History" />
        </Tabs>
      </Paper>

      {/* Pending Movements Tab */}
      <TabPanel value={currentTab} index={0}>
        <Card>
          <CardHeader 
            title="Pending Movements"
            action={
              <IconButton onClick={() => queryClient.invalidateQueries({ queryKey: ['pending-movements'] })}>
                <RefreshIcon />
              </IconButton>
            }
          />
          <CardContent>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Product</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Location</TableCell>
                    <TableCell align="right">Expected</TableCell>
                    <TableCell align="right">Scanned</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Operator</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {pendingMovements?.map((movement) => (
                    <TableRow key={movement.id}>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" fontWeight="medium">{movement.product_name}</Typography>
                          <Typography variant="caption" color="text.secondary">{movement.product_code}</Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          icon={getMovementTypeIcon(movement.movement_type)}
                          label={movement.movement_type}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {movement.location}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight="medium">
                          {movement.expected_quantity}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography 
                          variant="body2" 
                          color={movement.scanned_quantity === movement.expected_quantity ? 'success.main' : 'warning.main'}
                          fontWeight="medium"
                        >
                          {movement.scanned_quantity}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={movement.status}
                          size="small"
                          color={getStatusColor(movement.status) as any}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{movement.operator}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption">
                          {new Date(movement.created_at).toLocaleString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Stack direction="row" spacing={1}>
                          <Button
                            size="small"
                            variant="outlined"
                            startIcon={<QrIcon />}
                            onClick={startQRScanner}
                          >
                            Scan
                          </Button>
                          <Button
                            size="small"
                            variant="contained"
                            startIcon={<CompleteIcon />}
                            onClick={() => completeMovementMutation.mutate(movement.id)}
                            disabled={movement.scanned_quantity !== movement.expected_quantity}
                          >
                            Complete
                          </Button>
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

      {/* All Movements Tab */}
      <TabPanel value={currentTab} index={1}>
        <Card>
          <CardHeader title="All Stock Movements" />
          <CardContent>
            {movementsLoading ? (
              <LinearProgress />
            ) : (
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
                      <TableCell>Reference</TableCell>
                      <TableCell>Operator</TableCell>
                      <TableCell>Status</TableCell>
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
                            <Typography variant="body2" fontWeight="medium">{movement.product_name}</Typography>
                            <Typography variant="caption" color="text.secondary">{movement.product_code}</Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip
                            icon={getMovementTypeIcon(movement.movement_type)}
                            label={movement.movement_type}
                            size="small"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {movement.from_location || '—'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {movement.to_location || '—'}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" fontWeight="medium">
                            {movement.quantity}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">{movement.reference_number}</Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">{movement.operator}</Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={movement.status}
                            size="small"
                            color={getStatusColor(movement.status) as any}
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      </TabPanel>

      {/* Batch Processing Tab */}
      <TabPanel value={currentTab} index={2}>
        <Card>
          <CardHeader title="Batch Movement Processing" />
          <CardContent>
            <Stepper activeStep={currentStep} sx={{ mb: 4 }}>
              {movementSteps.map((label) => (
                <Step key={label}>
                  <StepLabel>{label}</StepLabel>
                </Step>
              ))}
            </Stepper>

            {currentStep === 0 && (
              <Box textAlign="center" py={4}>
                <Avatar sx={{ bgcolor: 'primary.main', width: 80, height: 80, mx: 'auto', mb: 2 }}>
                  <QrIcon sx={{ fontSize: 40 }} />
                </Avatar>
                <Typography variant="h5" gutterBottom>Start Scanning Items</Typography>
                <Typography variant="body1" color="text.secondary" paragraph>
                  Use the QR scanner to scan products for batch processing
                </Typography>
                <Button
                  variant="contained"
                  size="large"
                  startIcon={<QrIcon />}
                  onClick={startQRScanner}
                >
                  Start Batch Scan
                </Button>
              </Box>
            )}

            {currentStep > 0 && (
              <Alert severity="info">
                Batch processing steps would be implemented here with real QR scanning integration.
              </Alert>
            )}
          </CardContent>
        </Card>
      </TabPanel>

      {/* Movement History Tab */}
      <TabPanel value={currentTab} index={3}>
        <Card>
          <CardHeader title="Movement History & Analytics" />
          <CardContent>
            <Alert severity="info">
              Historical movement analytics and reporting features coming soon.
            </Alert>
          </CardContent>
        </Card>
      </TabPanel>

      {/* New Movement Dialog */}
      <Dialog open={movementDialogOpen} onClose={() => setMovementDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create New Stock Movement</DialogTitle>
        <DialogContent>
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Movement Type</InputLabel>
                <Select
                  value={newMovement.movement_type}
                  onChange={(e) => setNewMovement(prev => ({ ...prev, movement_type: e.target.value }))}
                  label="Movement Type"
                >
                  <MenuItem value="receive">Receive</MenuItem>
                  <MenuItem value="ship">Ship</MenuItem>
                  <MenuItem value="transfer">Transfer</MenuItem>
                  <MenuItem value="adjustment">Adjustment</MenuItem>
                  <MenuItem value="cycle_count">Cycle Count</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={6}>
              <Autocomplete
                options={products || []}
                getOptionLabel={(option) => `${option.name} (${option.code})`}
                renderInput={(params) => (
                  <TextField {...params} label="Product" fullWidth />
                )}
                onChange={(_, value) => {
                  setNewMovement(prev => ({
                    ...prev,
                    product_id: value?.id?.toString() || ''
                  }));
                }}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                label="Quantity"
                type="number"
                fullWidth
                value={newMovement.quantity}
                onChange={(e) => setNewMovement(prev => ({ ...prev, quantity: e.target.value }))}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <Autocomplete
                options={locations || []}
                getOptionLabel={(option) => option.full_location || option}
                renderInput={(params) => (
                  <TextField {...params} label="Location" fullWidth />
                )}
                onChange={(_, value) => {
                  setNewMovement(prev => ({
                    ...prev,
                    location: value?.full_location || value || ''
                  }));
                }}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                label="Reference Number"
                fullWidth
                value={newMovement.reference}
                onChange={(e) => setNewMovement(prev => ({ ...prev, reference: e.target.value }))}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                label="Unit Cost (optional)"
                type="number"
                fullWidth
                value={newMovement.unit_cost}
                onChange={(e) => setNewMovement(prev => ({ ...prev, unit_cost: e.target.value }))}
              />
            </Grid>

            {newMovement.movement_type === 'receive' && (
              <Grid item xs={12}>
                <TextField
                  label="Supplier (optional)"
                  fullWidth
                  value={newMovement.supplier}
                  onChange={(e) => setNewMovement(prev => ({ ...prev, supplier: e.target.value }))}
                />
              </Grid>
            )}

            <Grid item xs={12}>
              <TextField
                label="Notes (optional)"
                fullWidth
                multiline
                rows={3}
                value={newMovement.notes}
                onChange={(e) => setNewMovement(prev => ({ ...prev, notes: e.target.value }))}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMovementDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleSubmitMovement}
            variant="contained"
            disabled={
              createMovementMutation.isPending ||
              !newMovement.product_id ||
              !newMovement.quantity ||
              !newMovement.location
            }
          >
            {createMovementMutation.isPending ? 'Creating...' : 'Create Movement'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* QR Scanner Dialog */}
      <Dialog
        open={qrScannerOpen}
        onClose={stopQRScanner}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>QR Code Scanner</DialogTitle>
        <DialogContent>
          <Box position="relative" width="100%" height={300} bgcolor="black" display="flex" alignItems="center" justifyContent="center">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
            <canvas ref={canvasRef} style={{ display: 'none' }} />
            
            {/* Scan overlay */}
            <Box
              position="absolute"
              top="50%"
              left="50%"
              width={200}
              height={200}
              border="2px solid white"
              borderRadius={2}
              sx={{
                transform: 'translate(-50%, -50%)',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: -2,
                  left: -2,
                  right: -2,
                  bottom: -2,
                  border: '2px solid red',
                  borderRadius: 2,
                  animation: 'pulse 2s infinite'
                }
              }}
            />
          </Box>
          
          <Typography variant="body2" color="text.secondary" textAlign="center" sx={{ mt: 2 }}>
            Position the QR code within the scanning area
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={stopQRScanner}>Cancel</Button>
          <Button
            onClick={captureQRCode}
            variant="contained"
            startIcon={<CameraIcon />}
          >
            Capture
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StockMovementPage;