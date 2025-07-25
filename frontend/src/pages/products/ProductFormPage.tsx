import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm, Controller } from 'react-hook-form';
import {
  Box,
  Paper,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Button,
  Grid,
  Chip,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Alert,
  LinearProgress,
  InputAdornment,
  Tabs,
  Tab,
  Autocomplete,
  Stack
} from '@mui/material';
import {
  Save as SaveIcon,
  Cancel as CancelIcon,
  CloudUpload as UploadIcon,
  Image as ImageIcon,
  AttachFile as AttachIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import { apiClient } from '@/services/api';

interface ProductFormData {
  code: string;
  name: string;
  display_name: string;
  sku: string;
  standard_price: number;
  cost_price?: number;
  sale_price?: number;
  status: 'active' | 'inactive' | 'discontinued';
  product_type: 'product' | 'service' | 'kit';
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
  tags?: string[];
  images?: File[];
  attachments?: File[];
}

interface Product extends ProductFormData {
  id: number;
  created_at: string;
  updated_at: string;
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

export const ProductFormPage: React.FC = () => {
  const { productId } = useParams<{ productId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isEditing = !!productId;
  
  const [currentTab, setCurrentTab] = useState(0);
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const [attachmentFiles, setAttachmentFiles] = useState<File[]>([]);

  const {
    control,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors, isDirty, isSubmitting },
  } = useForm<ProductFormData>({
    defaultValues: {
      status: 'active',
      product_type: 'product',
      is_active: true,
      is_purchasable: true,
      is_sellable: true,
      is_trackable: true,
      tags: [],
    },
  });

  // Watch fields for dynamic updates
  const watchedName = watch('name');
  const watchedType = watch('product_type');

  // Fetch product data for editing
  const { data: product, isLoading } = useQuery({
    queryKey: ['product', productId],
    queryFn: async (): Promise<Product> => {
      const response = await apiClient.get(`/api/v1/products-basic/${productId}`);
      return response.data;
    },
    enabled: isEditing,
  });

  // Fetch categories for autocomplete
  const { data: categories } = useQuery({
    queryKey: ['product-categories'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/products-basic/categories');
      return response.data || [];
    },
  });

  // Fetch suppliers for autocomplete
  const { data: suppliers } = useQuery({
    queryKey: ['suppliers'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/suppliers');
      return response.data || [];
    },
  });

  // Populate form with existing product data
  useEffect(() => {
    if (product && isEditing) {
      reset({
        code: product.code,
        name: product.name,
        display_name: product.display_name,
        sku: product.sku,
        standard_price: product.standard_price,
        cost_price: product.cost_price,
        sale_price: product.sale_price,
        status: product.status,
        product_type: product.product_type,
        description: product.description || '',
        category: product.category || '',
        weight: product.weight,
        length: product.length,
        width: product.width,
        height: product.height,
        barcode: product.barcode || '',
        supplier: product.supplier || '',
        lead_time_days: product.lead_time_days,
        minimum_stock_level: product.minimum_stock_level,
        reorder_point: product.reorder_point,
        is_active: product.is_active,
        is_purchasable: product.is_purchasable,
        is_sellable: product.is_sellable,
        is_trackable: product.is_trackable,
        tags: product.tags || [],
      });
    }
  }, [product, reset, isEditing]);

  // Auto-generate display name from name
  useEffect(() => {
    if (watchedName && !watch('display_name')) {
      setValue('display_name', watchedName, { shouldDirty: true });
    }
  }, [watchedName, setValue, watch]);

  // Create/Update mutation
  const mutation = useMutation({
    mutationFn: async (data: ProductFormData) => {
      const formData = new FormData();
      
      // Append form fields
      Object.entries(data).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach((item, index) => {
              formData.append(`${key}[${index}]`, item);
            });
          } else {
            formData.append(key, value.toString());
          }
        }
      });

      // Append files
      imageFiles.forEach((file, index) => {
        formData.append(`images[${index}]`, file);
      });
      
      attachmentFiles.forEach((file, index) => {
        formData.append(`attachments[${index}]`, file);
      });

      if (isEditing) {
        const response = await apiClient.put(`/api/v1/products-basic/${productId}`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
      } else {
        const response = await apiClient.post('/api/v1/products-basic', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
      }
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['products-list'] });
      queryClient.invalidateQueries({ queryKey: ['product', productId] });
      navigate(isEditing ? `/products/${productId}` : `/products/${result.id}`);
    },
  });

  const onSubmit = async (data: ProductFormData) => {
    await mutation.mutateAsync(data);
  };

  const handleCancel = () => {
    navigate(isEditing ? `/products/${productId}` : '/products');
  };

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    setImageFiles(prev => [...prev, ...files]);
  };

  const handleAttachmentUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    setAttachmentFiles(prev => [...prev, ...files]);
  };

  const removeImage = (index: number) => {
    setImageFiles(prev => prev.filter((_, i) => i !== index));
  };

  const removeAttachment = (index: number) => {
    setAttachmentFiles(prev => prev.filter((_, i) => i !== index));
  };

  if (isEditing && isLoading) {
    return (
      <Box p={3}>
        <LinearProgress />
        <Typography>Loading product...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          {isEditing ? 'Edit Product' : 'Create New Product'}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {isEditing ? 'Update product information' : 'Add a new product to your catalog'}
        </Typography>
      </Paper>

      <form onSubmit={handleSubmit(onSubmit)}>
        {/* Tab Navigation */}
        <Paper sx={{ mb: 3 }}>
          <Tabs
            value={currentTab}
            onChange={(_, newValue) => setCurrentTab(newValue)}
            variant="scrollable"
            scrollButtons="auto"
          >
            <Tab label="Basic Information" />
            <Tab label="Pricing & Finance" />
            <Tab label="Inventory & Stock" />
            <Tab label="Physical Properties" />
            <Tab label="Media & Attachments" />
            <Tab label="Settings & Options" />
          </Tabs>
        </Paper>

        {/* Basic Information Tab */}
        <TabPanel value={currentTab} index={0}>
          <Card>
            <CardHeader title="Basic Information" />
            <CardContent>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Controller
                    name="code"
                    control={control}
                    rules={{ 
                      required: 'Product code is required',
                      pattern: {
                        value: /^[A-Z0-9_-]+$/,
                        message: 'Code must contain only uppercase letters, numbers, hyphens, and underscores'
                      }
                    }}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Product Code"
                        error={!!errors.code}
                        helperText={errors.code?.message}
                        fullWidth
                        required
                      />
                    )}
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <Controller
                    name="sku"
                    control={control}
                    rules={{ required: 'SKU is required' }}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="SKU"
                        error={!!errors.sku}
                        helperText={errors.sku?.message}
                        fullWidth
                        required
                      />
                    )}
                  />
                </Grid>

                <Grid item xs={12}>
                  <Controller
                    name="name"
                    control={control}
                    rules={{ required: 'Product name is required' }}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Product Name"
                        error={!!errors.name}
                        helperText={errors.name?.message}
                        fullWidth
                        required
                      />
                    )}
                  />
                </Grid>

                <Grid item xs={12}>
                  <Controller
                    name="display_name"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Display Name"
                        helperText="If empty, will use the product name"
                        fullWidth
                      />
                    )}
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <Controller
                    name="category"
                    control={control}
                    render={({ field }) => (
                      <Autocomplete
                        {...field}
                        options={categories || []}
                        freeSolo
                        onChange={(_, value) => field.onChange(value)}
                        renderInput={(params) => (
                          <TextField
                            {...params}
                            label="Category"
                            fullWidth
                          />
                        )}
                      />
                    )}
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <Controller
                    name="barcode"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Barcode"
                        fullWidth
                      />
                    )}
                  />
                </Grid>

                <Grid item xs={12}>
                  <Controller
                    name="description"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Description"
                        multiline
                        rows={4}
                        fullWidth
                      />
                    )}
                  />
                </Grid>

                <Grid item xs={12}>
                  <Controller
                    name="tags"
                    control={control}
                    render={({ field }) => (
                      <Autocomplete
                        {...field}
                        multiple
                        freeSolo
                        options={[]}
                        onChange={(_, value) => field.onChange(value)}
                        renderTags={(value, getTagProps) =>
                          value.map((option, index) => (
                            <Chip variant="outlined" label={option} {...getTagProps({ index })} />
                          ))
                        }
                        renderInput={(params) => (
                          <TextField
                            {...params}
                            label="Tags"
                            placeholder="Add tags..."
                            fullWidth
                          />
                        )}
                      />
                    )}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </TabPanel>

        {/* Pricing Tab */}
        <TabPanel value={currentTab} index={1}>
          <Card>
            <CardHeader title="Pricing & Finance" />
            <CardContent>
              <Grid container spacing={3}>
                <Grid item xs={12} md={4}>
                  <Controller
                    name="standard_price"
                    control={control}
                    rules={{ 
                      required: 'Standard price is required',
                      min: { value: 0, message: 'Price must be positive' }
                    }}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Standard Price"
                        type="number"
                        InputProps={{
                          startAdornment: <InputAdornment position="start">$</InputAdornment>,
                        }}
                        error={!!errors.standard_price}
                        helperText={errors.standard_price?.message}
                        fullWidth
                        required
                      />
                    )}
                  />
                </Grid>

                <Grid item xs={12} md={4}>
                  <Controller
                    name="cost_price"
                    control={control}
                    rules={{ min: { value: 0, message: 'Cost price must be positive' } }}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Cost Price"
                        type="number"
                        InputProps={{
                          startAdornment: <InputAdornment position="start">$</InputAdornment>,
                        }}
                        error={!!errors.cost_price}
                        helperText={errors.cost_price?.message}
                        fullWidth
                      />
                    )}
                  />
                </Grid>

                <Grid item xs={12} md={4}>
                  <Controller
                    name="sale_price"
                    control={control}
                    rules={{ min: { value: 0, message: 'Sale price must be positive' } }}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Sale Price"
                        type="number"
                        InputProps={{
                          startAdornment: <InputAdornment position="start">$</InputAdornment>,
                        }}
                        error={!!errors.sale_price}
                        helperText={errors.sale_price?.message}
                        fullWidth
                      />
                    )}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </TabPanel>

        {/* Inventory Tab */}
        <TabPanel value={currentTab} index={2}>
          <Card>
            <CardHeader title="Inventory & Stock Management" />
            <CardContent>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Controller
                    name="supplier"
                    control={control}
                    render={({ field }) => (
                      <Autocomplete
                        {...field}
                        options={suppliers || []}
                        freeSolo
                        onChange={(_, value) => field.onChange(value)}
                        renderInput={(params) => (
                          <TextField
                            {...params}
                            label="Supplier"
                            fullWidth
                          />
                        )}
                      />
                    )}
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <Controller
                    name="lead_time_days"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Lead Time (days)"
                        type="number"
                        fullWidth
                      />
                    )}
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <Controller
                    name="minimum_stock_level"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Minimum Stock Level"
                        type="number"
                        fullWidth
                      />
                    )}
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <Controller
                    name="reorder_point"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Reorder Point"
                        type="number"
                        fullWidth
                      />
                    )}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </TabPanel>

        {/* Physical Properties Tab */}
        <TabPanel value={currentTab} index={3}>
          <Card>
            <CardHeader title="Physical Properties" />
            <CardContent>
              <Grid container spacing={3}>
                <Grid item xs={12} md={3}>
                  <Controller
                    name="weight"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Weight"
                        type="number"
                        InputProps={{
                          endAdornment: <InputAdornment position="end">kg</InputAdornment>,
                        }}
                        fullWidth
                      />
                    )}
                  />
                </Grid>

                <Grid item xs={12} md={3}>
                  <Controller
                    name="length"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Length"
                        type="number"
                        InputProps={{
                          endAdornment: <InputAdornment position="end">cm</InputAdornment>,
                        }}
                        fullWidth
                      />
                    )}
                  />
                </Grid>

                <Grid item xs={12} md={3}>
                  <Controller
                    name="width"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Width"
                        type="number"
                        InputProps={{
                          endAdornment: <InputAdornment position="end">cm</InputAdornment>,
                        }}
                        fullWidth
                      />
                    )}
                  />
                </Grid>

                <Grid item xs={12} md={3}>
                  <Controller
                    name="height"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Height"
                        type="number"
                        InputProps={{
                          endAdornment: <InputAdornment position="end">cm</InputAdornment>,
                        }}
                        fullWidth
                      />
                    )}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </TabPanel>

        {/* Media & Attachments Tab */}
        <TabPanel value={currentTab} index={4}>
          <Grid container spacing={3}>
            {/* Images */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardHeader 
                  title="Product Images"
                  action={
                    <Button
                      component="label"
                      startIcon={<ImageIcon />}
                      variant="outlined"
                      size="small"
                    >
                      Add Images
                      <input
                        type="file"
                        hidden
                        multiple
                        accept="image/*"
                        onChange={handleImageUpload}
                      />
                    </Button>
                  }
                />
                <CardContent>
                  <Stack spacing={2}>
                    {imageFiles.map((file, index) => (
                      <Box key={index} display="flex" alignItems="center" justifyContent="space-between">
                        <Typography variant="body2">{file.name}</Typography>
                        <Button
                          size="small"
                          color="error"
                          onClick={() => removeImage(index)}
                        >
                          <DeleteIcon />
                        </Button>
                      </Box>
                    ))}
                    {imageFiles.length === 0 && (
                      <Typography variant="body2" color="text.secondary">
                        No images uploaded
                      </Typography>
                    )}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            {/* Attachments */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardHeader 
                  title="Attachments"
                  action={
                    <Button
                      component="label"
                      startIcon={<AttachIcon />}
                      variant="outlined"
                      size="small"
                    >
                      Add Files
                      <input
                        type="file"
                        hidden
                        multiple
                        onChange={handleAttachmentUpload}
                      />
                    </Button>
                  }
                />
                <CardContent>
                  <Stack spacing={2}>
                    {attachmentFiles.map((file, index) => (
                      <Box key={index} display="flex" alignItems="center" justifyContent="space-between">
                        <Typography variant="body2">{file.name}</Typography>
                        <Button
                          size="small"
                          color="error"
                          onClick={() => removeAttachment(index)}
                        >
                          <DeleteIcon />
                        </Button>
                      </Box>
                    ))}
                    {attachmentFiles.length === 0 && (
                      <Typography variant="body2" color="text.secondary">
                        No attachments uploaded
                      </Typography>
                    )}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Settings Tab */}
        <TabPanel value={currentTab} index={5}>
          <Card>
            <CardHeader title="Product Settings" />
            <CardContent>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Controller
                    name="status"
                    control={control}
                    render={({ field }) => (
                      <FormControl fullWidth>
                        <InputLabel>Status</InputLabel>
                        <Select {...field} label="Status">
                          <MenuItem value="active">Active</MenuItem>
                          <MenuItem value="inactive">Inactive</MenuItem>
                          <MenuItem value="discontinued">Discontinued</MenuItem>
                        </Select>
                      </FormControl>
                    )}
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <Controller
                    name="product_type"
                    control={control}
                    render={({ field }) => (
                      <FormControl fullWidth>
                        <InputLabel>Product Type</InputLabel>
                        <Select {...field} label="Product Type">
                          <MenuItem value="product">Product</MenuItem>
                          <MenuItem value="service">Service</MenuItem>
                          <MenuItem value="kit">Kit</MenuItem>
                        </Select>
                      </FormControl>
                    )}
                  />
                </Grid>

                <Grid item xs={12}>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Capabilities
                  </Typography>
                </Grid>

                <Grid item xs={12} md={3}>
                  <Controller
                    name="is_active"
                    control={control}
                    render={({ field }) => (
                      <FormControlLabel
                        control={<Switch {...field} checked={field.value} />}
                        label="Active"
                      />
                    )}
                  />
                </Grid>

                <Grid item xs={12} md={3}>
                  <Controller
                    name="is_purchasable"
                    control={control}
                    render={({ field }) => (
                      <FormControlLabel
                        control={<Switch {...field} checked={field.value} />}
                        label="Can be purchased"
                      />
                    )}
                  />
                </Grid>

                <Grid item xs={12} md={3}>
                  <Controller
                    name="is_sellable"
                    control={control}
                    render={({ field }) => (
                      <FormControlLabel
                        control={<Switch {...field} checked={field.value} />}
                        label="Can be sold"
                      />
                    )}
                  />
                </Grid>

                <Grid item xs={12} md={3}>
                  <Controller
                    name="is_trackable"
                    control={control}
                    render={({ field }) => (
                      <FormControlLabel
                        control={<Switch {...field} checked={field.value} />}
                        label="Track inventory"
                      />
                    )}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </TabPanel>

        {/* Form Actions */}
        <Paper sx={{ p: 3, mt: 3 }}>
          <Stack direction="row" spacing={2} justifyContent="flex-end">
            <Button
              variant="outlined"
              onClick={handleCancel}
              disabled={isSubmitting}
            >
              <CancelIcon sx={{ mr: 1 }} />
              Cancel
            </Button>
            
            <Button
              type="submit"
              variant="contained"
              disabled={isSubmitting || !isDirty}
              startIcon={isSubmitting ? <LinearProgress size={20} /> : <SaveIcon />}
            >
              {isSubmitting ? 'Saving...' : isEditing ? 'Update Product' : 'Create Product'}
            </Button>
          </Stack>
        </Paper>

        {/* Error Display */}
        {mutation.error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {mutation.error instanceof Error ? mutation.error.message : 'An error occurred'}
          </Alert>
        )}
      </form>
    </Box>
  );
};

export default ProductFormPage;