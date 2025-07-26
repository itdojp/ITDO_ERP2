import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Box,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  CardHeader,
  Grid,
  LinearProgress,
  Alert,
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
  IconButton,
  Stack,
  Divider,
  FormControlLabel,
  Switch,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from "@mui/material";
import {
  CloudUpload as UploadIcon,
  Download as DownloadIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  ArrowBack as BackIcon,
  Preview as PreviewIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  GetApp as TemplateIcon,
} from "@mui/icons-material";
import { apiClient } from "@/services/api";

interface ImportPreview {
  valid_rows: number;
  invalid_rows: number;
  total_rows: number;
  errors: ImportError[];
  warnings: ImportWarning[];
  sample_data: ProductImportRow[];
}

interface ImportError {
  row: number;
  field: string;
  message: string;
  value: string;
}

interface ImportWarning {
  row: number;
  field: string;
  message: string;
  value: string;
}

interface ProductImportRow {
  row_number: number;
  code: string;
  name: string;
  sku: string;
  standard_price: number;
  cost_price?: number;
  sale_price?: number;
  status: string;
  product_type: string;
  description?: string;
  category?: string;
  weight?: number;
  length?: number;
  width?: number;
  height?: number;
  barcode?: string;
  supplier?: string;
  lead_time_days?: number;
  minimum_stock_level?: number;
  reorder_point?: number;
  is_active: boolean;
  is_purchasable: boolean;
  is_sellable: boolean;
  is_trackable: boolean;
  validation_status: "valid" | "warning" | "error";
  validation_messages: string[];
}

interface ImportResult {
  success: boolean;
  imported_count: number;
  failed_count: number;
  errors: ImportError[];
  duration_seconds: number;
}

export const ProductImportPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [importPreview, setImportPreview] = useState<ImportPreview | null>(
    null,
  );
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [importStep, setImportStep] = useState<
    "upload" | "preview" | "importing" | "complete"
  >("upload");

  // Import options
  const [updateExisting, setUpdateExisting] = useState(false);
  const [skipInvalid, setSkipInvalid] = useState(true);
  const [defaultStatus, setDefaultStatus] = useState("active");
  const [defaultType, setDefaultType] = useState("product");

  // File upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (file: File): Promise<ImportPreview> => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("preview_only", "true");

      const response = await apiClient.post(
        "/api/v1/products-basic/import",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        },
      );
      return response.data;
    },
    onSuccess: (data) => {
      setImportPreview(data);
      setImportStep("preview");
    },
  });

  // Import execution mutation
  const importMutation = useMutation({
    mutationFn: async (): Promise<ImportResult> => {
      if (!selectedFile) throw new Error("No file selected");

      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("update_existing", updateExisting.toString());
      formData.append("skip_invalid", skipInvalid.toString());
      formData.append("default_status", defaultStatus);
      formData.append("default_type", defaultType);

      const response = await apiClient.post(
        "/api/v1/products-basic/import",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        },
      );
      return response.data;
    },
    onSuccess: (data) => {
      setImportResult(data);
      setImportStep("complete");
      queryClient.invalidateQueries({ queryKey: ["products-list"] });
    },
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setImportPreview(null);
      setImportResult(null);
      setImportStep("upload");
    }
  };

  const handleUpload = async () => {
    if (selectedFile) {
      await uploadMutation.mutateAsync(selectedFile);
    }
  };

  const handleImport = async () => {
    setImportStep("importing");
    await importMutation.mutateAsync();
  };

  const handleDownloadTemplate = () => {
    // Create CSV template
    const headers = [
      "code",
      "name",
      "sku",
      "standard_price",
      "cost_price",
      "sale_price",
      "status",
      "product_type",
      "description",
      "category",
      "weight",
      "length",
      "width",
      "height",
      "barcode",
      "supplier",
      "lead_time_days",
      "minimum_stock_level",
      "reorder_point",
      "is_active",
      "is_purchasable",
      "is_sellable",
      "is_trackable",
    ];

    const sampleRow = [
      "PROD001",
      "Sample Product",
      "SKU001",
      "99.99",
      "49.99",
      "89.99",
      "active",
      "product",
      "Sample product description",
      "Electronics",
      "1.5",
      "10",
      "15",
      "20",
      "1234567890123",
      "Sample Supplier",
      "7",
      "10",
      "5",
      "true",
      "true",
      "true",
      "true",
    ];

    const csvContent = [headers.join(","), sampleRow.join(",")].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "product_import_template.csv";
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleReset = () => {
    setSelectedFile(null);
    setImportPreview(null);
    setImportResult(null);
    setImportStep("upload");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const getStatusColor = (status: "valid" | "warning" | "error") => {
    switch (status) {
      case "valid":
        return "success";
      case "warning":
        return "warning";
      case "error":
        return "error";
      default:
        return "default";
    }
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: "auto", p: 3 }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          mb={2}
        >
          <Stack direction="row" alignItems="center" spacing={2}>
            <IconButton onClick={() => navigate("/products")}>
              <BackIcon />
            </IconButton>
            <Box>
              <Typography variant="h4" component="h1">
                Import Products
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Import products from CSV file with validation and preview
              </Typography>
            </Box>
          </Stack>

          <Stack direction="row" spacing={2}>
            <Button
              variant="outlined"
              startIcon={<TemplateIcon />}
              onClick={handleDownloadTemplate}
            >
              Download Template
            </Button>
            {importStep !== "upload" && (
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={handleReset}
              >
                Start Over
              </Button>
            )}
          </Stack>
        </Stack>

        {/* Progress Indicator */}
        <Stack direction="row" spacing={2} alignItems="center">
          <Chip
            label="1. Upload"
            color={importStep === "upload" ? "primary" : "default"}
            variant={importStep === "upload" ? "filled" : "outlined"}
          />
          <Chip
            label="2. Preview"
            color={importStep === "preview" ? "primary" : "default"}
            variant={importStep === "preview" ? "filled" : "outlined"}
          />
          <Chip
            label="3. Import"
            color={importStep === "importing" ? "primary" : "default"}
            variant={importStep === "importing" ? "filled" : "outlined"}
          />
          <Chip
            label="4. Complete"
            color={importStep === "complete" ? "success" : "default"}
            variant={importStep === "complete" ? "filled" : "outlined"}
          />
        </Stack>
      </Paper>

      {/* Step 1: File Upload */}
      {importStep === "upload" && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardHeader title="Upload CSV File" />
              <CardContent>
                <Box
                  sx={{
                    border: "2px dashed",
                    borderColor: "grey.300",
                    borderRadius: 2,
                    p: 4,
                    textAlign: "center",
                    cursor: "pointer",
                    "&:hover": {
                      borderColor: "primary.main",
                      bgcolor: "action.hover",
                    },
                  }}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    onChange={handleFileSelect}
                    style={{ display: "none" }}
                  />
                  <UploadIcon sx={{ fontSize: 48, color: "grey.400", mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    {selectedFile
                      ? selectedFile.name
                      : "Choose CSV file to upload"}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Drag and drop or click to select your product CSV file
                  </Typography>
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    Supported formats: CSV, Excel (.xlsx, .xls)
                  </Typography>
                </Box>

                {selectedFile && (
                  <Box sx={{ mt: 3 }}>
                    <Alert severity="info" sx={{ mb: 2 }}>
                      File selected: {selectedFile.name} (
                      {(selectedFile.size / 1024).toFixed(1)} KB)
                    </Alert>
                    <Button
                      variant="contained"
                      startIcon={<PreviewIcon />}
                      onClick={handleUpload}
                      disabled={uploadMutation.isPending}
                      fullWidth
                    >
                      {uploadMutation.isPending
                        ? "Processing..."
                        : "Preview Import"}
                    </Button>
                  </Box>
                )}

                {uploadMutation.error && (
                  <Alert severity="error" sx={{ mt: 2 }}>
                    Failed to process file. Please check the format and try
                    again.
                  </Alert>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card>
              <CardHeader title="Import Guidelines" />
              <CardContent>
                <Typography variant="body2" paragraph>
                  <strong>Required Fields:</strong>
                </Typography>
                <Typography
                  variant="body2"
                  component="ul"
                  sx={{ pl: 2, mb: 2 }}
                >
                  <li>code (unique product code)</li>
                  <li>name (product name)</li>
                  <li>sku (stock keeping unit)</li>
                  <li>standard_price (numeric value)</li>
                </Typography>

                <Typography variant="body2" paragraph>
                  <strong>Optional Fields:</strong>
                </Typography>
                <Typography
                  variant="body2"
                  component="ul"
                  sx={{ pl: 2, mb: 2 }}
                >
                  <li>cost_price, sale_price</li>
                  <li>description, category</li>
                  <li>weight, dimensions</li>
                  <li>barcode, supplier</li>
                  <li>inventory settings</li>
                </Typography>

                <Typography variant="body2" paragraph>
                  <strong>Boolean Fields:</strong>
                </Typography>
                <Typography variant="body2" sx={{ pl: 2 }}>
                  Use 'true' or 'false' for is_active, is_purchasable,
                  is_sellable, is_trackable
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Step 2: Preview */}
      {importStep === "preview" && importPreview && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardHeader
                title="Import Preview"
                action={
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setPreviewDialogOpen(true)}
                  >
                    View Details
                  </Button>
                }
              />
              <CardContent>
                <Grid container spacing={3} sx={{ mb: 3 }}>
                  <Grid item xs={12} md={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="primary">
                        {importPreview.total_rows}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Rows
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="success.main">
                        {importPreview.valid_rows}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Valid Rows
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="warning.main">
                        {importPreview.warnings.length}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Warnings
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="error.main">
                        {importPreview.errors.length}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Errors
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>

                {importPreview.errors.length > 0 && (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    Found {importPreview.errors.length} validation errors.
                    Please fix these before importing.
                  </Alert>
                )}

                {importPreview.warnings.length > 0 && (
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    Found {importPreview.warnings.length} warnings. Review these
                    before proceeding.
                  </Alert>
                )}

                {importPreview.valid_rows > 0 && (
                  <Alert severity="success" sx={{ mb: 2 }}>
                    {importPreview.valid_rows} rows are ready for import.
                  </Alert>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={8}>
            <Card>
              <CardHeader title="Import Options" />
              <CardContent>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={updateExisting}
                          onChange={(e) => setUpdateExisting(e.target.checked)}
                        />
                      }
                      label="Update existing products"
                    />
                    <Typography
                      variant="caption"
                      display="block"
                      color="text.secondary"
                    >
                      Update products with matching codes
                    </Typography>
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={skipInvalid}
                          onChange={(e) => setSkipInvalid(e.target.checked)}
                        />
                      }
                      label="Skip invalid rows"
                    />
                    <Typography
                      variant="caption"
                      display="block"
                      color="text.secondary"
                    >
                      Continue import even with errors
                    </Typography>
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth>
                      <InputLabel>Default Status</InputLabel>
                      <Select
                        value={defaultStatus}
                        onChange={(e) => setDefaultStatus(e.target.value)}
                        label="Default Status"
                      >
                        <MenuItem value="active">Active</MenuItem>
                        <MenuItem value="inactive">Inactive</MenuItem>
                        <MenuItem value="discontinued">Discontinued</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth>
                      <InputLabel>Default Type</InputLabel>
                      <Select
                        value={defaultType}
                        onChange={(e) => setDefaultType(e.target.value)}
                        label="Default Type"
                      >
                        <MenuItem value="product">Product</MenuItem>
                        <MenuItem value="service">Service</MenuItem>
                        <MenuItem value="kit">Kit</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>

                <Divider sx={{ my: 3 }} />

                <Stack direction="row" spacing={2} justifyContent="flex-end">
                  <Button
                    variant="outlined"
                    onClick={() => setImportStep("upload")}
                  >
                    Back to Upload
                  </Button>
                  <Button
                    variant="contained"
                    onClick={handleImport}
                    disabled={importPreview.errors.length > 0 && !skipInvalid}
                    startIcon={<UploadIcon />}
                  >
                    Import {importPreview.valid_rows} Products
                  </Button>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card>
              <CardHeader title="Quick Summary" />
              <CardContent>
                <Stack spacing={2}>
                  {importPreview.errors.slice(0, 3).map((error, index) => (
                    <Alert key={index} severity="error" variant="outlined">
                      <Typography variant="body2">
                        Row {error.row}: {error.message}
                      </Typography>
                    </Alert>
                  ))}
                  {importPreview.warnings.slice(0, 3).map((warning, index) => (
                    <Alert key={index} severity="warning" variant="outlined">
                      <Typography variant="body2">
                        Row {warning.row}: {warning.message}
                      </Typography>
                    </Alert>
                  ))}
                  {(importPreview.errors.length > 3 ||
                    importPreview.warnings.length > 3) && (
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      textAlign="center"
                    >
                      View details for complete list
                    </Typography>
                  )}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Step 3: Importing */}
      {importStep === "importing" && (
        <Card>
          <CardContent sx={{ textAlign: "center", py: 6 }}>
            <LinearProgress sx={{ mb: 3 }} />
            <Typography variant="h5" gutterBottom>
              Importing Products...
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Please wait while we process your import. This may take a few
              moments.
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Step 4: Complete */}
      {importStep === "complete" && importResult && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent sx={{ textAlign: "center", py: 4 }}>
                {importResult.success ? (
                  <>
                    <SuccessIcon
                      sx={{ fontSize: 64, color: "success.main", mb: 2 }}
                    />
                    <Typography variant="h4" gutterBottom>
                      Import Complete!
                    </Typography>
                    <Typography
                      variant="body1"
                      color="text.secondary"
                      paragraph
                    >
                      Successfully imported {importResult.imported_count}{" "}
                      products
                      {importResult.failed_count > 0 &&
                        ` (${importResult.failed_count} failed)`}
                    </Typography>
                  </>
                ) : (
                  <>
                    <ErrorIcon
                      sx={{ fontSize: 64, color: "error.main", mb: 2 }}
                    />
                    <Typography variant="h4" gutterBottom>
                      Import Failed
                    </Typography>
                    <Typography
                      variant="body1"
                      color="text.secondary"
                      paragraph
                    >
                      The import process encountered errors and could not
                      complete.
                    </Typography>
                  </>
                )}

                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 3 }}
                >
                  Import completed in {importResult.duration_seconds.toFixed(1)}{" "}
                  seconds
                </Typography>

                <Stack direction="row" spacing={2} justifyContent="center">
                  <Button
                    variant="contained"
                    onClick={() => navigate("/products")}
                  >
                    View Products
                  </Button>
                  <Button variant="outlined" onClick={handleReset}>
                    Import More
                  </Button>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          {importResult.errors.length > 0 && (
            <Grid item xs={12}>
              <Card>
                <CardHeader title="Import Errors" />
                <CardContent>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Row</TableCell>
                          <TableCell>Field</TableCell>
                          <TableCell>Error</TableCell>
                          <TableCell>Value</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {importResult.errors.map((error, index) => (
                          <TableRow key={index}>
                            <TableCell>{error.row}</TableCell>
                            <TableCell>{error.field}</TableCell>
                            <TableCell>{error.message}</TableCell>
                            <TableCell>{error.value}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      )}

      {/* Preview Dialog */}
      <Dialog
        open={previewDialogOpen}
        onClose={() => setPreviewDialogOpen(false)}
        maxWidth="xl"
        fullWidth
      >
        <DialogTitle>
          Import Preview Details
          <IconButton
            onClick={() => setPreviewDialogOpen(false)}
            sx={{ position: "absolute", right: 8, top: 8 }}
          >
            <DeleteIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {importPreview && (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Row</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Code</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>SKU</TableCell>
                    <TableCell>Price</TableCell>
                    <TableCell>Issues</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {importPreview.sample_data.map((row) => (
                    <TableRow key={row.row_number}>
                      <TableCell>{row.row_number}</TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={row.validation_status}
                          color={getStatusColor(row.validation_status)}
                        />
                      </TableCell>
                      <TableCell>{row.code}</TableCell>
                      <TableCell>{row.name}</TableCell>
                      <TableCell>{row.sku}</TableCell>
                      <TableCell>${row.standard_price?.toFixed(2)}</TableCell>
                      <TableCell>
                        {row.validation_messages.map((msg, idx) => (
                          <Typography
                            key={idx}
                            variant="caption"
                            display="block"
                            color="error"
                          >
                            {msg}
                          </Typography>
                        ))}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ProductImportPage;
