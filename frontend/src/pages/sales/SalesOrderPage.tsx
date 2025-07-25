import React, { useState, useEffect, useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm, Controller, useFieldArray } from "react-hook-form";
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  TextField,
  Button,
  IconButton,
  Stack,
  Divider,
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
  Autocomplete,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Avatar,
  Alert,
  LinearProgress,
  InputAdornment,
  Stepper,
  Step,
  StepLabel,
  Tabs,
  Tab,
} from "@mui/material";
import {
  Add as AddIcon,
  Remove as RemoveIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Person as CustomerIcon,
  ShoppingCart as ProductIcon,
  Receipt as OrderIcon,
  LocalShipping as ShippingIcon,
  Payment as PaymentIcon,
  Calculate as CalculateIcon,
  Save as SaveIcon,
  Send as SendIcon,
  Print as PrintIcon,
  Email as EmailIcon,
  Edit as EditIcon,
  ContentCopy as CopyIcon,
  CheckCircle as CompleteIcon,
  Cancel as CancelIcon,
  Inventory as StockIcon,
} from "@mui/icons-material";
import { apiClient } from "@/services/api";

interface Customer {
  id: number;
  code: string;
  name: string;
  email: string;
  phone: string;
  address: string;
  tax_id?: string;
  credit_limit?: number;
  payment_terms?: string;
  discount_rate?: number;
}

interface Product {
  id: number;
  code: string;
  name: string;
  description?: string;
  price: number;
  cost_price?: number;
  available_stock: number;
  unit: string;
  tax_rate: number;
  category?: string;
}

interface OrderItem {
  id?: number;
  product_id: number;
  product_code: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  discount_percent: number;
  discount_amount: number;
  tax_rate: number;
  tax_amount: number;
  line_total: number;
  notes?: string;
}

interface SalesOrder {
  id?: number;
  order_number: string;
  customer_id: number;
  customer_name: string;
  order_date: string;
  delivery_date?: string;
  status:
    | "draft"
    | "pending"
    | "confirmed"
    | "shipped"
    | "delivered"
    | "cancelled";
  payment_terms: string;
  shipping_method: string;
  shipping_address: string;
  billing_address: string;
  items: OrderItem[];
  subtotal: number;
  discount_amount: number;
  tax_amount: number;
  shipping_cost: number;
  total_amount: number;
  notes?: string;
  internal_notes?: string;
  created_by: string;
  created_at?: string;
  updated_at?: string;
}

interface OrderFormData {
  customer_id: number | null;
  order_date: string;
  delivery_date: string;
  payment_terms: string;
  shipping_method: string;
  shipping_address: string;
  billing_address: string;
  notes: string;
  internal_notes: string;
  items: OrderItem[];
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

export const SalesOrderPage: React.FC = () => {
  const { orderId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isEditing = !!orderId;

  const [currentTab, setCurrentTab] = useState(0);
  const [customerDialogOpen, setCustomerDialogOpen] = useState(false);
  const [productDialogOpen, setProductDialogOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(
    null,
  );

  const orderSteps = [
    "Customer & Basic Info",
    "Add Products",
    "Review & Pricing",
    "Confirm Order",
  ];

  const {
    control,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors, isDirty, isSubmitting },
  } = useForm<OrderFormData>({
    defaultValues: {
      customer_id: null,
      order_date: new Date().toISOString().split("T")[0],
      delivery_date: "",
      payment_terms: "NET30",
      shipping_method: "standard",
      shipping_address: "",
      billing_address: "",
      notes: "",
      internal_notes: "",
      items: [],
    },
  });

  const {
    fields: itemFields,
    append: addItem,
    remove: removeItem,
    update: updateItem,
  } = useFieldArray({
    control,
    name: "items",
  });

  // Watch form values for calculations
  const watchedItems = watch("items");
  const watchedCustomerId = watch("customer_id");

  // Fetch existing order for editing
  const { data: existingOrder, isLoading: orderLoading } = useQuery({
    queryKey: ["sales-order", orderId],
    queryFn: async (): Promise<SalesOrder> => {
      const response = await apiClient.get(`/api/v1/sales-orders/${orderId}`);
      return response.data;
    },
    enabled: isEditing,
  });

  // Fetch customers
  const { data: customers } = useQuery({
    queryKey: ["customers"],
    queryFn: async (): Promise<Customer[]> => {
      const response = await apiClient.get("/api/v1/customers");
      return response.data || [];
    },
  });

  // Fetch products
  const { data: products } = useQuery({
    queryKey: ["products-sales"],
    queryFn: async (): Promise<Product[]> => {
      const response = await apiClient.get("/api/v1/products-basic");
      return response.data || [];
    },
  });

  // Calculate totals
  const calculations = useMemo(() => {
    const subtotal =
      watchedItems?.reduce((sum, item) => {
        return sum + item.quantity * item.unit_price;
      }, 0) || 0;

    const totalDiscount =
      watchedItems?.reduce((sum, item) => {
        const lineDiscount =
          (item.quantity * item.unit_price * (item.discount_percent || 0)) /
          100;
        return sum + lineDiscount;
      }, 0) || 0;

    const subtotalAfterDiscount = subtotal - totalDiscount;

    const totalTax =
      watchedItems?.reduce((sum, item) => {
        const lineSubtotal = item.quantity * item.unit_price;
        const lineDiscount =
          (lineSubtotal * (item.discount_percent || 0)) / 100;
        const lineTax =
          ((lineSubtotal - lineDiscount) * (item.tax_rate || 0)) / 100;
        return sum + lineTax;
      }, 0) || 0;

    const shippingCost = 0; // Could be calculated based on shipping method
    const totalAmount = subtotalAfterDiscount + totalTax + shippingCost;

    return {
      subtotal,
      totalDiscount,
      subtotalAfterDiscount,
      totalTax,
      shippingCost,
      totalAmount,
    };
  }, [watchedItems]);

  // Update line totals when items change
  useEffect(() => {
    watchedItems?.forEach((item, index) => {
      const lineSubtotal = item.quantity * item.unit_price;
      const discountAmount =
        (lineSubtotal * (item.discount_percent || 0)) / 100;
      const taxableAmount = lineSubtotal - discountAmount;
      const taxAmount = (taxableAmount * (item.tax_rate || 0)) / 100;
      const lineTotal = taxableAmount + taxAmount;

      updateItem(index, {
        ...item,
        discount_amount: discountAmount,
        tax_amount: taxAmount,
        line_total: lineTotal,
      });
    });
  }, [watchedItems, updateItem]);

  // Load customer data when selected
  useEffect(() => {
    if (watchedCustomerId && customers) {
      const customer = customers.find((c) => c.id === watchedCustomerId);
      if (customer) {
        setSelectedCustomer(customer);
        setValue("shipping_address", customer.address);
        setValue("billing_address", customer.address);
        setValue("payment_terms", customer.payment_terms || "NET30");
      }
    }
  }, [watchedCustomerId, customers, setValue]);

  // Populate form with existing order data
  useEffect(() => {
    if (existingOrder && isEditing) {
      reset({
        customer_id: existingOrder.customer_id,
        order_date: existingOrder.order_date,
        delivery_date: existingOrder.delivery_date || "",
        payment_terms: existingOrder.payment_terms,
        shipping_method: existingOrder.shipping_method,
        shipping_address: existingOrder.shipping_address,
        billing_address: existingOrder.billing_address,
        notes: existingOrder.notes || "",
        internal_notes: existingOrder.internal_notes || "",
        items: existingOrder.items,
      });
    }
  }, [existingOrder, reset, isEditing]);

  // Create/Update order mutation
  const orderMutation = useMutation({
    mutationFn: async (data: OrderFormData) => {
      const orderData = {
        ...data,
        subtotal: calculations.subtotal,
        discount_amount: calculations.totalDiscount,
        tax_amount: calculations.totalTax,
        shipping_cost: calculations.shippingCost,
        total_amount: calculations.totalAmount,
        status: "draft",
      };

      if (isEditing) {
        const response = await apiClient.put(
          `/api/v1/sales-orders/${orderId}`,
          orderData,
        );
        return response.data;
      } else {
        const response = await apiClient.post(
          "/api/v1/sales-orders",
          orderData,
        );
        return response.data;
      }
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["sales-orders"] });
      if (!isEditing) {
        navigate(`/sales/orders/${result.id}`);
      }
    },
  });

  // Confirm order mutation
  const confirmOrderMutation = useMutation({
    mutationFn: async () => {
      await apiClient.post(`/api/v1/sales-orders/${orderId}/confirm`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sales-order", orderId] });
      queryClient.invalidateQueries({ queryKey: ["sales-orders"] });
    },
  });

  const handleAddProduct = (product: Product) => {
    const existingItemIndex = itemFields.findIndex(
      (item) => item.product_id === product.id,
    );

    if (existingItemIndex >= 0) {
      // Increase quantity if product already exists
      const existingItem = itemFields[existingItemIndex];
      updateItem(existingItemIndex, {
        ...existingItem,
        quantity: existingItem.quantity + 1,
      });
    } else {
      // Add new product
      addItem({
        product_id: product.id,
        product_code: product.code,
        product_name: product.name,
        quantity: 1,
        unit_price: product.price,
        discount_percent: selectedCustomer?.discount_rate || 0,
        discount_amount: 0,
        tax_rate: product.tax_rate,
        tax_amount: 0,
        line_total: 0,
        notes: "",
      });
    }
    setProductDialogOpen(false);
  };

  const handleSubmitOrder = async (data: OrderFormData) => {
    await orderMutation.mutateAsync(data);
  };

  const handleConfirmOrder = async () => {
    await confirmOrderMutation.mutateAsync();
  };

  const duplicateOrder = () => {
    navigate("/sales/orders/new", {
      state: { duplicateFrom: orderId },
    });
  };

  if (isEditing && orderLoading) {
    return (
      <Box sx={{ maxWidth: 1200, mx: "auto", p: 3 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2 }}>Loading order...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1400, mx: "auto", p: 3 }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          mb={2}
        >
          <Typography variant="h4" component="h1">
            {isEditing
              ? `Edit Order ${existingOrder?.order_number}`
              : "Create Sales Order"}
          </Typography>

          <Stack direction="row" spacing={2}>
            {isEditing && (
              <>
                <Button
                  variant="outlined"
                  startIcon={<CopyIcon />}
                  onClick={duplicateOrder}
                >
                  Duplicate
                </Button>
                <Button variant="outlined" startIcon={<PrintIcon />}>
                  Print
                </Button>
                <Button variant="outlined" startIcon={<EmailIcon />}>
                  Email
                </Button>
                {existingOrder?.status === "draft" && (
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<CompleteIcon />}
                    onClick={handleConfirmOrder}
                    disabled={confirmOrderMutation.isPending}
                  >
                    Confirm Order
                  </Button>
                )}
              </>
            )}
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSubmit(handleSubmitOrder)}
              disabled={isSubmitting || !isDirty}
            >
              {isSubmitting
                ? "Saving..."
                : isEditing
                  ? "Update Order"
                  : "Save Draft"}
            </Button>
          </Stack>
        </Stack>

        {/* Order Status */}
        {isEditing && existingOrder && (
          <Stack direction="row" spacing={2} alignItems="center">
            <Chip
              label={existingOrder.status.toUpperCase()}
              color={
                existingOrder.status === "confirmed"
                  ? "success"
                  : existingOrder.status === "shipped"
                    ? "info"
                    : existingOrder.status === "cancelled"
                      ? "error"
                      : "warning"
              }
            />
            <Typography variant="body2" color="text.secondary">
              Created:{" "}
              {existingOrder.created_at
                ? new Date(existingOrder.created_at).toLocaleString()
                : "—"}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Updated:{" "}
              {existingOrder.updated_at
                ? new Date(existingOrder.updated_at).toLocaleString()
                : "—"}
            </Typography>
          </Stack>
        )}

        {/* Progress Stepper for New Orders */}
        {!isEditing && (
          <Stepper activeStep={currentStep} sx={{ mt: 3 }}>
            {orderSteps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        )}
      </Paper>

      <form onSubmit={handleSubmit(handleSubmitOrder)}>
        <Grid container spacing={3}>
          {/* Left Column */}
          <Grid item xs={12} lg={8}>
            {/* Customer Information */}
            <Card sx={{ mb: 3 }}>
              <CardHeader
                title="Customer Information"
                action={
                  <Button
                    startIcon={<SearchIcon />}
                    onClick={() => setCustomerDialogOpen(true)}
                  >
                    Select Customer
                  </Button>
                }
              />
              <CardContent>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Controller
                      name="customer_id"
                      control={control}
                      rules={{ required: "Customer is required" }}
                      render={({ field }) => (
                        <Autocomplete
                          options={customers || []}
                          getOptionLabel={(option) =>
                            `${option.name} (${option.code})`
                          }
                          value={
                            customers?.find((c) => c.id === field.value) || null
                          }
                          onChange={(_, value) =>
                            field.onChange(value?.id || null)
                          }
                          renderInput={(params) => (
                            <TextField
                              {...params}
                              label="Customer"
                              error={!!errors.customer_id}
                              helperText={errors.customer_id?.message}
                              required
                            />
                          )}
                        />
                      )}
                    />
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <Controller
                      name="order_date"
                      control={control}
                      rules={{ required: "Order date is required" }}
                      render={({ field }) => (
                        <TextField
                          {...field}
                          label="Order Date"
                          type="date"
                          error={!!errors.order_date}
                          helperText={errors.order_date?.message}
                          fullWidth
                          required
                          InputLabelProps={{ shrink: true }}
                        />
                      )}
                    />
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <Controller
                      name="delivery_date"
                      control={control}
                      render={({ field }) => (
                        <TextField
                          {...field}
                          label="Delivery Date"
                          type="date"
                          fullWidth
                          InputLabelProps={{ shrink: true }}
                        />
                      )}
                    />
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <Controller
                      name="payment_terms"
                      control={control}
                      render={({ field }) => (
                        <FormControl fullWidth>
                          <InputLabel>Payment Terms</InputLabel>
                          <Select {...field} label="Payment Terms">
                            <MenuItem value="COD">Cash on Delivery</MenuItem>
                            <MenuItem value="NET15">Net 15 Days</MenuItem>
                            <MenuItem value="NET30">Net 30 Days</MenuItem>
                            <MenuItem value="NET60">Net 60 Days</MenuItem>
                            <MenuItem value="NET90">Net 90 Days</MenuItem>
                          </Select>
                        </FormControl>
                      )}
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <Controller
                      name="shipping_address"
                      control={control}
                      render={({ field }) => (
                        <TextField
                          {...field}
                          label="Shipping Address"
                          multiline
                          rows={3}
                          fullWidth
                        />
                      )}
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>

            {/* Order Items */}
            <Card>
              <CardHeader
                title="Order Items"
                action={
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setProductDialogOpen(true)}
                  >
                    Add Product
                  </Button>
                }
              />
              <CardContent>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Product</TableCell>
                        <TableCell align="right">Qty</TableCell>
                        <TableCell align="right">Unit Price</TableCell>
                        <TableCell align="right">Discount %</TableCell>
                        <TableCell align="right">Tax %</TableCell>
                        <TableCell align="right">Line Total</TableCell>
                        <TableCell align="center">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {itemFields.map((item, index) => (
                        <TableRow key={item.id}>
                          <TableCell>
                            <Box>
                              <Typography variant="body2" fontWeight="medium">
                                {item.product_name}
                              </Typography>
                              <Typography
                                variant="caption"
                                color="text.secondary"
                              >
                                {item.product_code}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <Controller
                              name={`items.${index}.quantity`}
                              control={control}
                              render={({ field }) => (
                                <TextField
                                  {...field}
                                  type="number"
                                  size="small"
                                  inputProps={{ min: 1 }}
                                  sx={{ width: 80 }}
                                />
                              )}
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Controller
                              name={`items.${index}.unit_price`}
                              control={control}
                              render={({ field }) => (
                                <TextField
                                  {...field}
                                  type="number"
                                  size="small"
                                  inputProps={{ step: 0.01, min: 0 }}
                                  InputProps={{
                                    startAdornment: (
                                      <InputAdornment position="start">
                                        $
                                      </InputAdornment>
                                    ),
                                  }}
                                  sx={{ width: 100 }}
                                />
                              )}
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Controller
                              name={`items.${index}.discount_percent`}
                              control={control}
                              render={({ field }) => (
                                <TextField
                                  {...field}
                                  type="number"
                                  size="small"
                                  inputProps={{ step: 0.1, min: 0, max: 100 }}
                                  sx={{ width: 70 }}
                                />
                              )}
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Controller
                              name={`items.${index}.tax_rate`}
                              control={control}
                              render={({ field }) => (
                                <TextField
                                  {...field}
                                  type="number"
                                  size="small"
                                  inputProps={{ step: 0.1, min: 0, max: 100 }}
                                  sx={{ width: 70 }}
                                />
                              )}
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" fontWeight="medium">
                              ${item.line_total?.toFixed(2) || "0.00"}
                            </Typography>
                          </TableCell>
                          <TableCell align="center">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => removeItem(index)}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                      {itemFields.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={7} align="center">
                            <Typography color="text.secondary">
                              No items added. Click "Add Product" to get
                              started.
                            </Typography>
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>

          {/* Right Column */}
          <Grid item xs={12} lg={4}>
            {/* Order Summary */}
            <Card sx={{ mb: 3 }}>
              <CardHeader title="Order Summary" />
              <CardContent>
                <Stack spacing={2}>
                  <Box display="flex" justifyContent="space-between">
                    <Typography>Subtotal:</Typography>
                    <Typography>${calculations.subtotal.toFixed(2)}</Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between">
                    <Typography>Discount:</Typography>
                    <Typography color="error">
                      -${calculations.totalDiscount.toFixed(2)}
                    </Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between">
                    <Typography>Tax:</Typography>
                    <Typography>${calculations.totalTax.toFixed(2)}</Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between">
                    <Typography>Shipping:</Typography>
                    <Typography>
                      ${calculations.shippingCost.toFixed(2)}
                    </Typography>
                  </Box>
                  <Divider />
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="h6">Total:</Typography>
                    <Typography variant="h6" color="primary">
                      ${calculations.totalAmount.toFixed(2)}
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>

            {/* Customer Details */}
            {selectedCustomer && (
              <Card sx={{ mb: 3 }}>
                <CardHeader title="Customer Details" />
                <CardContent>
                  <Stack spacing={2}>
                    <Box>
                      <Typography variant="subtitle2">Name</Typography>
                      <Typography>{selectedCustomer.name}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="subtitle2">Email</Typography>
                      <Typography>{selectedCustomer.email}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="subtitle2">Phone</Typography>
                      <Typography>{selectedCustomer.phone}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="subtitle2">Credit Limit</Typography>
                      <Typography>
                        ${selectedCustomer.credit_limit?.toFixed(2) || "0.00"}
                      </Typography>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            )}

            {/* Notes */}
            <Card>
              <CardHeader title="Notes" />
              <CardContent>
                <Stack spacing={3}>
                  <Controller
                    name="notes"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Customer Notes"
                        multiline
                        rows={3}
                        fullWidth
                        helperText="Notes visible to customer"
                      />
                    )}
                  />
                  <Controller
                    name="internal_notes"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Internal Notes"
                        multiline
                        rows={3}
                        fullWidth
                        helperText="Internal notes (not visible to customer)"
                      />
                    )}
                  />
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </form>

      {/* Customer Selection Dialog */}
      <Dialog
        open={customerDialogOpen}
        onClose={() => setCustomerDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Select Customer</DialogTitle>
        <DialogContent>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Code</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Phone</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {customers?.map((customer) => (
                  <TableRow key={customer.id}>
                    <TableCell>{customer.code}</TableCell>
                    <TableCell>{customer.name}</TableCell>
                    <TableCell>{customer.email}</TableCell>
                    <TableCell>{customer.phone}</TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        onClick={() => {
                          setValue("customer_id", customer.id);
                          setCustomerDialogOpen(false);
                        }}
                      >
                        Select
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCustomerDialogOpen(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>

      {/* Product Selection Dialog */}
      <Dialog
        open={productDialogOpen}
        onClose={() => setProductDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Add Products</DialogTitle>
        <DialogContent>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Code</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell align="right">Price</TableCell>
                  <TableCell align="right">Stock</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {products?.map((product) => (
                  <TableRow key={product.id}>
                    <TableCell>
                      <Typography variant="body2" fontFamily="monospace">
                        {product.code}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight="medium">
                          {product.name}
                        </Typography>
                        {product.description && (
                          <Typography variant="caption" color="text.secondary">
                            {product.description}
                          </Typography>
                        )}
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">
                        ${product.price.toFixed(2)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Chip
                        label={product.available_stock}
                        size="small"
                        color={
                          product.available_stock > 0 ? "success" : "error"
                        }
                        icon={<StockIcon />}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {product.category || "—"}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        variant="contained"
                        onClick={() => handleAddProduct(product)}
                        disabled={product.available_stock <= 0}
                      >
                        Add
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setProductDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SalesOrderPage;
