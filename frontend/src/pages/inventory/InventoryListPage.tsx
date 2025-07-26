import React, { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  DataGrid,
  GridColDef,
  GridRowSelectionModel,
  GridToolbar,
  GridActionsCellItem,
} from "@mui/x-data-grid";
import {
  Box,
  Paper,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Button,
  IconButton,
  Drawer,
  Stack,
  Card,
  CardContent,
  Divider,
  Alert,
  LinearProgress,
  Badge,
  Avatar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Autocomplete,
} from "@mui/material";
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Add as AddIcon,
  Inventory as InventoryIcon,
  Warning as WarningIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Refresh as RefreshIcon,
  QrCodeScanner as QrIcon,
  LocationOn as LocationIcon,
  Assignment as MovementIcon,
  Analytics as AnalyticsIcon,
  Sync as SyncIcon,
  NotificationImportant as AlertIcon,
  Download as ExportIcon,
} from "@mui/icons-material";
import {
  useInventory,
  useInventoryStats,
  useInventoryLocations,
  useAdjustStock,
  useTransferStock,
} from "../../hooks/useInventory";
import { InventoryItem } from "../../services/api/inventory";

interface InventoryFilters {
  search: string;
  stock_status: string;
  warehouse_location: string;
  category: string;
  supplier: string;
  movement_trend: string;
  stock_min: string;
  stock_max: string;
  value_min: string;
  value_max: string;
}

export const InventoryListPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [selectedRows, setSelectedRows] = useState<GridRowSelectionModel>([]);
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false);
  const [adjustmentDialogOpen, setAdjustmentDialogOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);
  const [adjustmentQuantity, setAdjustmentQuantity] = useState("");
  const [adjustmentReason, setAdjustmentReason] = useState("");
  const [adjustmentNotes, setAdjustmentNotes] = useState("");

  const [paginationModel, setPaginationModel] = useState({
    page: 0,
    pageSize: 25,
  });

  const [filters, setFilters] = useState<InventoryFilters>({
    search: "",
    stock_status: "",
    warehouse_location: "",
    category: "",
    supplier: "",
    movement_trend: "",
    stock_min: "",
    stock_max: "",
    value_min: "",
    value_max: "",
  });

  // Auto refresh every 30 seconds for real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      queryClient.invalidateQueries({ queryKey: ["inventory-list"] });
    }, 30000);
    return () => clearInterval(interval);
  }, [queryClient]);

  // API query parameters
  const queryParams = useMemo(() => {
    const params: any = {
      page: paginationModel.page + 1,
      per_page: paginationModel.pageSize,
      sort_by: "created_at",
      sort_order: "desc",
    };

    if (filters.search) params.search = filters.search;
    if (filters.stock_status) params.status = filters.stock_status;
    if (filters.warehouse_location)
      params.location = filters.warehouse_location;
    if (filters.stock_min) params.min_quantity = parseInt(filters.stock_min);
    if (filters.stock_max) params.max_quantity = parseInt(filters.stock_max);

    return params;
  }, [paginationModel, filters]);

  // Fetch inventory data with real-time updates
  const {
    data: inventoryData,
    isLoading,
    error,
    refetch,
  } = useInventory(queryParams);
  const { data: inventoryStats } = useInventoryStats();
  const { data: locations } = useInventoryLocations();
  const adjustStockMutation = useAdjustStock();
  const transferStockMutation = useTransferStock();

  const items = inventoryData?.items || [];
  const totalItems = inventoryData?.total || 0;

  // Stock adjustment mutation
  const adjustmentMutation = useMutation({
    mutationFn: async (adjustment: StockAdjustment) => {
      await apiClient.post("/api/v1/inventory/adjust", adjustment);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventory-list"] });
      setAdjustmentDialogOpen(false);
      setSelectedItem(null);
      setAdjustmentQuantity("");
      setAdjustmentReason("");
      setAdjustmentNotes("");
    },
  });

  // Bulk stock sync mutation
  const syncMutation = useMutation({
    mutationFn: async (productIds: number[]) => {
      await apiClient.post("/api/v1/inventory/sync", {
        product_ids: productIds,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventory-list"] });
      setSelectedRows([]);
    },
  });

  // DataGrid columns configuration
  const columns: GridColDef[] = useMemo(
    () => [
      {
        field: "product_code",
        headerName: "Code",
        width: 120,
        renderCell: (params) => (
          <Typography
            variant="body2"
            fontFamily="monospace"
            fontWeight="medium"
          >
            {params.value}
          </Typography>
        ),
      },
      {
        field: "product_name",
        headerName: "Product",
        width: 200,
        renderCell: (params) => (
          <Box>
            <Typography variant="body2" fontWeight="medium">
              {params.value}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {params.row.sku}
            </Typography>
          </Box>
        ),
      },
      {
        field: "warehouse_location",
        headerName: "Location",
        width: 130,
        renderCell: (params) => (
          <Box>
            <Typography variant="body2">{params.value || "—"}</Typography>
            {params.row.bin_location && (
              <Typography variant="caption" color="text.secondary">
                Bin: {params.row.bin_location}
              </Typography>
            )}
          </Box>
        ),
      },
      {
        field: "current_stock",
        headerName: "Current",
        width: 100,
        type: "number",
        renderCell: (params) => (
          <Box textAlign="center">
            <Typography variant="body2" fontWeight="medium">
              {params.value}
            </Typography>
            {params.row.movement_trend === "up" && (
              <TrendingUpIcon color="success" fontSize="small" />
            )}
            {params.row.movement_trend === "down" && (
              <TrendingDownIcon color="error" fontSize="small" />
            )}
          </Box>
        ),
      },
      {
        field: "available_stock",
        headerName: "Available",
        width: 100,
        type: "number",
        renderCell: (params) => (
          <Typography variant="body2" color="primary">
            {params.value}
          </Typography>
        ),
      },
      {
        field: "reserved_stock",
        headerName: "Reserved",
        width: 100,
        type: "number",
        renderCell: (params) => (
          <Typography
            variant="body2"
            color={params.value > 0 ? "warning.main" : "text.secondary"}
          >
            {params.value}
          </Typography>
        ),
      },
      {
        field: "stock_status",
        headerName: "Status",
        width: 120,
        renderCell: (params) => {
          const getStatusConfig = (status: string) => {
            switch (status) {
              case "in_stock":
                return { color: "success" as const, label: "In Stock" };
              case "low_stock":
                return { color: "warning" as const, label: "Low Stock" };
              case "out_of_stock":
                return { color: "error" as const, label: "Out of Stock" };
              case "overstock":
                return { color: "info" as const, label: "Overstock" };
              default:
                return { color: "default" as const, label: status };
            }
          };

          const { color, label } = getStatusConfig(params.value);
          return (
            <Chip label={label} size="small" color={color} variant="filled" />
          );
        },
      },
      {
        field: "stock_value",
        headerName: "Value",
        width: 110,
        type: "number",
        renderCell: (params) => (
          <Typography variant="body2" fontWeight="medium">
            ${params.value?.toFixed(2)}
          </Typography>
        ),
      },
      {
        field: "turnover_rate",
        headerName: "Turnover",
        width: 100,
        type: "number",
        renderCell: (params) => (
          <Typography variant="body2">{params.value?.toFixed(1)}x</Typography>
        ),
      },
      {
        field: "days_of_inventory",
        headerName: "DOI",
        width: 80,
        type: "number",
        renderCell: (params) => (
          <Typography variant="body2">
            {Math.round(params.value || 0)}d
          </Typography>
        ),
      },
      {
        field: "last_movement_date",
        headerName: "Last Movement",
        width: 130,
        renderCell: (params) => (
          <Typography variant="caption">
            {new Date(params.value).toLocaleDateString()}
          </Typography>
        ),
      },
      {
        field: "actions",
        type: "actions",
        headerName: "Actions",
        width: 120,
        getActions: (params) => [
          <GridActionsCellItem
            icon={<InventoryIcon />}
            label="Adjust"
            onClick={() => {
              setSelectedItem(params.row);
              setAdjustmentDialogOpen(true);
            }}
          />,
          <GridActionsCellItem
            icon={<MovementIcon />}
            label="History"
            onClick={() =>
              navigate(`/inventory/movements/${params.row.product_id}`)
            }
          />,
          <GridActionsCellItem
            icon={<LocationIcon />}
            label="Location"
            onClick={() =>
              navigate(`/warehouse/products/${params.row.product_id}`)
            }
          />,
        ],
      },
    ],
    [navigate],
  );

  // Event handlers
  const handleFilterChange = (field: keyof InventoryFilters, value: string) => {
    setFilters((prev) => ({ ...prev, [field]: value }));
    setPaginationModel((prev) => ({ ...prev, page: 0 }));
  };

  const handleClearFilters = () => {
    setFilters({
      search: "",
      stock_status: "",
      warehouse_location: "",
      category: "",
      supplier: "",
      movement_trend: "",
      stock_min: "",
      stock_max: "",
      value_min: "",
      value_max: "",
    });
  };

  const handleStockAdjustment = async () => {
    if (selectedItem && adjustmentQuantity && adjustmentReason) {
      await adjustmentMutation.mutateAsync({
        product_id: selectedItem.product_id,
        adjustment_quantity: parseFloat(adjustmentQuantity),
        reason: adjustmentReason,
        notes: adjustmentNotes,
      });
    }
  };

  const handleBulkSync = async () => {
    if (selectedRows.length > 0) {
      await syncMutation.mutateAsync(selectedRows as number[]);
    }
  };

  const handleExport = () => {
    // Export functionality
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value && value !== "") {
        params.append(key, value);
      }
    });
    window.open(`/api/v1/inventory/export?${params}`, "_blank");
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
        Filter Inventory
      </Typography>

      <Stack spacing={3}>
        <TextField
          label="Search"
          placeholder="Search by product name, code, or SKU..."
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
          <InputLabel>Stock Status</InputLabel>
          <Select
            value={filters.stock_status}
            onChange={(e) => handleFilterChange("stock_status", e.target.value)}
            label="Stock Status"
          >
            <MenuItem value="">All Status</MenuItem>
            <MenuItem value="in_stock">In Stock</MenuItem>
            <MenuItem value="low_stock">Low Stock</MenuItem>
            <MenuItem value="out_of_stock">Out of Stock</MenuItem>
            <MenuItem value="overstock">Overstock</MenuItem>
          </Select>
        </FormControl>

        <Autocomplete
          options={warehouses || []}
          getOptionLabel={(option) => option.name || option}
          value={filters.warehouse_location}
          onChange={(_, value) =>
            handleFilterChange("warehouse_location", value?.name || value || "")
          }
          renderInput={(params) => (
            <TextField {...params} label="Warehouse Location" fullWidth />
          )}
        />

        <Autocomplete
          options={categories || []}
          value={filters.category}
          onChange={(_, value) => handleFilterChange("category", value || "")}
          renderInput={(params) => (
            <TextField {...params} label="Category" fullWidth />
          )}
        />

        <Autocomplete
          options={suppliers || []}
          value={filters.supplier}
          onChange={(_, value) => handleFilterChange("supplier", value || "")}
          renderInput={(params) => (
            <TextField {...params} label="Supplier" fullWidth />
          )}
        />

        <FormControl fullWidth>
          <InputLabel>Movement Trend</InputLabel>
          <Select
            value={filters.movement_trend}
            onChange={(e) =>
              handleFilterChange("movement_trend", e.target.value)
            }
            label="Movement Trend"
          >
            <MenuItem value="">All Trends</MenuItem>
            <MenuItem value="up">Trending Up</MenuItem>
            <MenuItem value="down">Trending Down</MenuItem>
            <MenuItem value="stable">Stable</MenuItem>
          </Select>
        </FormControl>

        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Stock Range
          </Typography>
          <Stack direction="row" spacing={2}>
            <TextField
              label="Min Stock"
              type="number"
              value={filters.stock_min}
              onChange={(e) => handleFilterChange("stock_min", e.target.value)}
              size="small"
            />
            <TextField
              label="Max Stock"
              type="number"
              value={filters.stock_max}
              onChange={(e) => handleFilterChange("stock_max", e.target.value)}
              size="small"
            />
          </Stack>
        </Box>

        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Value Range
          </Typography>
          <Stack direction="row" spacing={2}>
            <TextField
              label="Min Value"
              type="number"
              value={filters.value_min}
              onChange={(e) => handleFilterChange("value_min", e.target.value)}
              size="small"
            />
            <TextField
              label="Max Value"
              type="number"
              value={filters.value_max}
              onChange={(e) => handleFilterChange("value_max", e.target.value)}
              size="small"
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
          Failed to load inventory data. Please try again.
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
          <Typography variant="h4" component="h1">
            Inventory Management
          </Typography>

          <Stack direction="row" spacing={2}>
            <IconButton onClick={() => refetch()} disabled={isLoading}>
              <RefreshIcon />
            </IconButton>

            <Button
              variant="outlined"
              startIcon={<FilterIcon />}
              onClick={() => setFilterDrawerOpen(true)}
              badge={activeFiltersCount > 0}
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
              variant="outlined"
              startIcon={<QrIcon />}
              onClick={() => navigate("/inventory/scan")}
            >
              QR Scan
            </Button>

            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => navigate("/inventory/adjustment")}
            >
              Stock Adjustment
            </Button>
          </Stack>
        </Box>

        {/* Key Metrics */}
        <Grid container spacing={3} sx={{ mb: 2 }}>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent
                sx={{ display: "flex", alignItems: "center", py: 2 }}
              >
                <Avatar sx={{ bgcolor: "primary.main", mr: 2 }}>
                  <InventoryIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    {inventoryData?.items.length || 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Total Items
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent
                sx={{ display: "flex", alignItems: "center", py: 2 }}
              >
                <Avatar sx={{ bgcolor: "success.main", mr: 2 }}>
                  <TrendingUpIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    ${inventoryData?.total_value?.toFixed(0) || "0"}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Total Value
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent
                sx={{ display: "flex", alignItems: "center", py: 2 }}
              >
                <Avatar sx={{ bgcolor: "warning.main", mr: 2 }}>
                  <WarningIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    {inventoryData?.low_stock_count || 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Low Stock
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent
                sx={{ display: "flex", alignItems: "center", py: 2 }}
              >
                <Avatar sx={{ bgcolor: "error.main", mr: 2 }}>
                  <AlertIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    {inventoryData?.alerts || 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Alerts
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Quick Search */}
        <TextField
          placeholder="Quick search inventory..."
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
                  {selectedRows.length} item{selectedRows.length > 1 ? "s" : ""}{" "}
                  selected
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
                    startIcon={<SyncIcon />}
                    onClick={handleBulkSync}
                    disabled={syncMutation.isPending}
                  >
                    Sync Stock
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
          rows={items}
          columns={columns}
          paginationModel={paginationModel}
          onPaginationModelChange={setPaginationModel}
          rowCount={totalItems}
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
            "& .MuiDataGrid-row": {
              '&[data-stock-status="out_of_stock"]': {
                bgcolor: "error.50",
              },
              '&[data-stock-status="low_stock"]': {
                bgcolor: "warning.50",
              },
            },
          }}
          getRowId={(row) => row.id}
        />
      </Paper>

      <FilterDrawer />

      {/* Stock Adjustment Dialog */}
      <Dialog
        open={adjustmentDialogOpen}
        onClose={() => setAdjustmentDialogOpen(false)}
      >
        <DialogTitle>Adjust Stock - {selectedItem?.product_name}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Current stock: {selectedItem?.current_stock || 0} units
          </Typography>
          <Stack spacing={2}>
            <TextField
              autoFocus
              label="Adjustment Quantity"
              type="number"
              fullWidth
              value={adjustmentQuantity}
              onChange={(e) => setAdjustmentQuantity(e.target.value)}
              helperText="Use positive numbers to add stock, negative to reduce"
            />
            <FormControl fullWidth>
              <InputLabel>Reason</InputLabel>
              <Select
                value={adjustmentReason}
                onChange={(e) => setAdjustmentReason(e.target.value)}
                label="Reason"
              >
                <MenuItem value="physical_count">Physical Count</MenuItem>
                <MenuItem value="damage">Damage</MenuItem>
                <MenuItem value="theft">Theft</MenuItem>
                <MenuItem value="expired">Expired</MenuItem>
                <MenuItem value="found">Found Stock</MenuItem>
                <MenuItem value="system_correction">System Correction</MenuItem>
                <MenuItem value="other">Other</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Notes (optional)"
              fullWidth
              multiline
              rows={3}
              value={adjustmentNotes}
              onChange={(e) => setAdjustmentNotes(e.target.value)}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAdjustmentDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleStockAdjustment}
            variant="contained"
            disabled={
              adjustmentMutation.isPending ||
              !adjustmentQuantity ||
              !adjustmentReason
            }
          >
            {adjustmentMutation.isPending ? "Adjusting..." : "Adjust Stock"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default InventoryListPage;
