# Page Templates Specifications

**Document ID**: ITDO-ERP-DD-PTS-001  
**Version**: 1.0  
**Date**: 2025-07-16  
**Author**: Claude Code AI  
**Issue**: #160  

---

## 1. Overview

This document defines comprehensive page template specifications for the ITDO ERP2 system, providing standardized layouts and patterns for all major page types. These templates ensure consistency, usability, and maintainability across the entire application.

## 2. Template Architecture

### 2.1 Base Layout Structure

#### 2.1.1 Application Shell

```typescript
interface AppShellStructure {
  header: {
    height: '64px';
    position: 'fixed';
    zIndex: 1000;
  };
  sidebar: {
    width: '240px';
    collapsedWidth: '60px';
    position: 'fixed';
    zIndex: 900;
  };
  main: {
    marginLeft: '240px'; // Adjusts based on sidebar state
    marginTop: '64px';
    minHeight: 'calc(100vh - 64px)';
  };
  footer: {
    height: '48px';
    position: 'sticky';
    bottom: 0;
  };
}
```

#### 2.1.2 Content Area Structure

```typescript
interface ContentAreaStructure {
  container: {
    maxWidth: '1200px';
    margin: '0 auto';
    padding: '24px';
  };
  pageHeader: {
    marginBottom: '32px';
    borderBottom: '1px solid #e5e7eb';
    paddingBottom: '16px';
  };
  pageContent: {
    minHeight: '400px';
    marginBottom: '24px';
  };
  pageFooter: {
    marginTop: '32px';
    borderTop: '1px solid #e5e7eb';
    paddingTop: '16px';
  };
}
```

### 2.2 Responsive Breakpoints

```typescript
interface ResponsiveBreakpoints {
  mobile: '320px - 767px';
  tablet: '768px - 1023px';
  desktop: '1024px - 1439px';
  largeDesktop: '1440px+';
}

interface ResponsiveBehavior {
  mobile: {
    sidebar: 'overlay';
    header: 'compact';
    padding: '16px';
    columns: 1;
  };
  tablet: {
    sidebar: 'collapsible';
    header: 'standard';
    padding: '20px';
    columns: 2;
  };
  desktop: {
    sidebar: 'persistent';
    header: 'full';
    padding: '24px';
    columns: 3;
  };
}
```

## 3. Authentication Templates

### 3.1 Login Page Template

#### 3.1.1 Layout Structure

```typescript
interface LoginPageLayout {
  container: {
    display: 'flex';
    minHeight: '100vh';
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
  };
  leftPanel: {
    width: '60%';
    display: 'flex';
    alignItems: 'center';
    justifyContent: 'center';
    padding: '48px';
  };
  rightPanel: {
    width: '40%';
    background: 'white';
    display: 'flex';
    alignItems: 'center';
    justifyContent: 'center';
    padding: '48px';
  };
  formContainer: {
    width: '100%';
    maxWidth: '400px';
  };
}
```

#### 3.1.2 Component Structure

```typescript
const LoginPageTemplate = () => {
  return (
    <div className="login-container">
      <div className="login-left-panel">
        <div className="brand-section">
          <Logo size="large" />
          <h1 className="brand-title">ITDO ERP System</h1>
          <p className="brand-description">
            Streamline your business operations with our comprehensive ERP solution
          </p>
        </div>
      </div>
      
      <div className="login-right-panel">
        <div className="login-form-container">
          <div className="form-header">
            <h2>Welcome Back</h2>
            <p>Sign in to your account</p>
          </div>
          
          <LoginForm />
          
          <div className="form-footer">
            <Link to="/forgot-password">Forgot your password?</Link>
            <div className="help-links">
              <Link to="/help">Need help?</Link>
              <Link to="/contact">Contact support</Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
```

#### 3.1.3 Form Components

```typescript
const LoginForm = () => {
  return (
    <form className="login-form">
      <FormField
        label="Email Address"
        required
        error={errors.email}
      >
        <Input
          type="email"
          prefixIcon={<Mail size="sm" />}
          placeholder="Enter your email"
          autoComplete="email"
        />
      </FormField>
      
      <FormField
        label="Password"
        required
        error={errors.password}
      >
        <Input
          type="password"
          prefixIcon={<Lock size="sm" />}
          suffixIcon={<Eye size="sm" />}
          placeholder="Enter your password"
          autoComplete="current-password"
        />
      </FormField>
      
      <div className="form-options">
        <Checkbox label="Remember me" />
        <Link to="/forgot-password">Forgot password?</Link>
      </div>
      
      <Button
        type="submit"
        variant="primary"
        size="lg"
        fullWidth
        loading={isSubmitting}
      >
        Sign In
      </Button>
    </form>
  );
};
```

### 3.2 Password Reset Template

#### 3.2.1 Multi-Step Layout

```typescript
const PasswordResetTemplate = () => {
  const [step, setStep] = useState<'request' | 'verify' | 'reset' | 'success'>('request');
  
  return (
    <div className="password-reset-container">
      <div className="reset-header">
        <Logo />
        <h1>Reset Your Password</h1>
        <ProgressSteps currentStep={step} />
      </div>
      
      <div className="reset-content">
        {step === 'request' && <RequestResetForm />}
        {step === 'verify' && <VerifyCodeForm />}
        {step === 'reset' && <NewPasswordForm />}
        {step === 'success' && <ResetSuccessMessage />}
      </div>
      
      <div className="reset-footer">
        <Link to="/login">Back to Login</Link>
      </div>
    </div>
  );
};
```

### 3.3 Two-Factor Authentication Template

#### 3.3.1 2FA Layout

```typescript
const TwoFactorAuthTemplate = () => {
  return (
    <div className="tfa-container">
      <div className="tfa-header">
        <Shield size="lg" color="primary" />
        <h2>Two-Factor Authentication</h2>
        <p>Please enter the verification code from your authenticator app</p>
      </div>
      
      <div className="tfa-form">
        <CodeInput
          length={6}
          placeholder="Enter 6-digit code"
          autoComplete="one-time-code"
        />
        
        <div className="tfa-actions">
          <Button variant="primary" size="lg" fullWidth>
            Verify Code
          </Button>
          
          <Button variant="ghost" size="sm">
            Resend Code
          </Button>
        </div>
      </div>
      
      <div className="tfa-alternatives">
        <Link to="/backup-codes">Use backup code</Link>
        <Link to="/contact-support">Contact support</Link>
      </div>
    </div>
  );
};
```

## 4. Dashboard Templates

### 4.1 Overview Dashboard Template

#### 4.1.1 Grid Layout

```typescript
interface DashboardGridLayout {
  container: {
    display: 'grid';
    gridTemplateColumns: 'repeat(12, 1fr)';
    gap: '24px';
    padding: '24px';
  };
  sections: {
    kpiCards: 'grid-column: 1 / -1';
    mainChart: 'grid-column: 1 / 9';
    sidebar: 'grid-column: 9 / -1';
    recentActivity: 'grid-column: 1 / 7';
    quickActions: 'grid-column: 7 / -1';
  };
}
```

#### 4.1.2 Component Structure

```typescript
const DashboardTemplate = () => {
  return (
    <div className="dashboard-container">
      <DashboardHeader />
      
      <div className="dashboard-content">
        <div className="dashboard-grid">
          {/* KPI Cards Section */}
          <section className="kpi-section">
            <div className="kpi-grid">
              <KPICard
                title="Total Revenue"
                value="$245,630"
                change="+12.5%"
                trend="up"
                icon={<DollarSign />}
              />
              <KPICard
                title="Active Users"
                value="1,429"
                change="+8.2%"
                trend="up"
                icon={<Users />}
              />
              <KPICard
                title="Orders"
                value="892"
                change="-3.1%"
                trend="down"
                icon={<Package />}
              />
              <KPICard
                title="Conversion Rate"
                value="3.24%"
                change="+0.5%"
                trend="up"
                icon={<TrendingUp />}
              />
            </div>
          </section>
          
          {/* Main Chart Section */}
          <section className="main-chart-section">
            <Card>
              <CardHeader>
                <h3>Revenue Trend</h3>
                <DateRangePicker />
              </CardHeader>
              <CardContent>
                <LineChart data={revenueData} />
              </CardContent>
            </Card>
          </section>
          
          {/* Sidebar Section */}
          <section className="dashboard-sidebar">
            <QuickStatsCard />
            <RecentAlertsCard />
          </section>
          
          {/* Recent Activity Section */}
          <section className="recent-activity-section">
            <Card>
              <CardHeader>
                <h3>Recent Activity</h3>
                <Button variant="ghost" size="sm">
                  View All
                </Button>
              </CardHeader>
              <CardContent>
                <ActivityList items={recentActivity} />
              </CardContent>
            </Card>
          </section>
          
          {/* Quick Actions Section */}
          <section className="quick-actions-section">
            <Card>
              <CardHeader>
                <h3>Quick Actions</h3>
              </CardHeader>
              <CardContent>
                <QuickActionGrid />
              </CardContent>
            </Card>
          </section>
        </div>
      </div>
    </div>
  );
};
```

#### 4.1.3 KPI Card Component

```typescript
interface KPICardProps {
  title: string;
  value: string;
  change: string;
  trend: 'up' | 'down' | 'neutral';
  icon: React.ReactNode;
  loading?: boolean;
}

const KPICard = ({ title, value, change, trend, icon, loading }: KPICardProps) => {
  return (
    <Card variant="elevated">
      <CardContent className="kpi-card-content">
        <div className="kpi-header">
          <div className="kpi-icon">{icon}</div>
          <div className="kpi-trend">
            <span className={`trend-indicator trend-${trend}`}>
              {trend === 'up' && <TrendingUp size="sm" />}
              {trend === 'down' && <TrendingDown size="sm" />}
              {change}
            </span>
          </div>
        </div>
        
        <div className="kpi-content">
          <h4 className="kpi-title">{title}</h4>
          <div className="kpi-value">{value}</div>
        </div>
        
        {loading && <LoadingOverlay />}
      </CardContent>
    </Card>
  );
};
```

### 4.2 Analytics Dashboard Template

#### 4.2.1 Advanced Layout

```typescript
const AnalyticsDashboardTemplate = () => {
  return (
    <div className="analytics-dashboard">
      <div className="dashboard-header">
        <h1>Analytics Dashboard</h1>
        <div className="dashboard-controls">
          <DateRangePicker />
          <Select
            options={departmentOptions}
            placeholder="All Departments"
          />
          <Button variant="outline">
            <Download size="sm" />
            Export
          </Button>
        </div>
      </div>
      
      <div className="analytics-grid">
        {/* Summary Cards */}
        <section className="summary-cards">
          <SummaryCard
            title="Total Sales"
            value="$1,234,567"
            comparison="vs last month"
            change="+15.3%"
          />
          <SummaryCard
            title="Conversion Rate"
            value="3.45%"
            comparison="vs last month"
            change="+0.8%"
          />
          <SummaryCard
            title="Customer Acquisition"
            value="234"
            comparison="vs last month"
            change="+22.1%"
          />
        </section>
        
        {/* Main Charts */}
        <section className="main-charts">
          <div className="chart-tabs">
            <Tabs defaultValue="revenue">
              <TabsList>
                <TabsTrigger value="revenue">Revenue</TabsTrigger>
                <TabsTrigger value="users">Users</TabsTrigger>
                <TabsTrigger value="orders">Orders</TabsTrigger>
              </TabsList>
              
              <TabsContent value="revenue">
                <LineChart data={revenueData} />
              </TabsContent>
              
              <TabsContent value="users">
                <AreaChart data={userData} />
              </TabsContent>
              
              <TabsContent value="orders">
                <BarChart data={orderData} />
              </TabsContent>
            </Tabs>
          </div>
        </section>
        
        {/* Side Charts */}
        <section className="side-charts">
          <Card>
            <CardHeader>
              <h3>Traffic Sources</h3>
            </CardHeader>
            <CardContent>
              <PieChart data={trafficData} />
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <h3>Top Products</h3>
            </CardHeader>
            <CardContent>
              <ProductList items={topProducts} />
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  );
};
```

## 5. List/Table View Templates

### 5.1 User Management Template

#### 5.1.1 List View Layout

```typescript
const UserManagementTemplate = () => {
  return (
    <div className="user-management-page">
      <PageHeader>
        <h1>User Management</h1>
        <div className="page-actions">
          <Button variant="outline">
            <Download size="sm" />
            Export
          </Button>
          <Button variant="primary">
            <Plus size="sm" />
            Add User
          </Button>
        </div>
      </PageHeader>
      
      <div className="page-content">
        <div className="filters-section">
          <SearchInput
            placeholder="Search users..."
            value={searchQuery}
            onChange={setSearchQuery}
          />
          
          <div className="filter-controls">
            <Select
              placeholder="Role"
              options={roleOptions}
              value={selectedRole}
              onChange={setSelectedRole}
            />
            
            <Select
              placeholder="Status"
              options={statusOptions}
              value={selectedStatus}
              onChange={setSelectedStatus}
            />
            
            <Select
              placeholder="Department"
              options={departmentOptions}
              value={selectedDepartment}
              onChange={setSelectedDepartment}
            />
          </div>
        </div>
        
        <div className="table-section">
          <UserTable
            data={filteredUsers}
            loading={isLoading}
            onSort={handleSort}
            onSelect={handleSelect}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        </div>
        
        <div className="pagination-section">
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
          />
        </div>
      </div>
    </div>
  );
};
```

#### 5.1.2 Table Configuration

```typescript
const userTableColumns = [
  {
    key: 'avatar',
    title: '',
    width: '60px',
    render: (user: User) => (
      <Avatar
        src={user.avatar}
        name={user.name}
        size="sm"
      />
    ),
  },
  {
    key: 'name',
    title: 'Name',
    sortable: true,
    render: (user: User) => (
      <div>
        <div className="font-medium">{user.name}</div>
        <div className="text-sm text-gray-500">{user.email}</div>
      </div>
    ),
  },
  {
    key: 'role',
    title: 'Role',
    sortable: true,
    render: (user: User) => (
      <Badge variant={user.role === 'admin' ? 'primary' : 'secondary'}>
        {user.role}
      </Badge>
    ),
  },
  {
    key: 'department',
    title: 'Department',
    sortable: true,
  },
  {
    key: 'status',
    title: 'Status',
    sortable: true,
    render: (user: User) => (
      <StatusBadge status={user.status} />
    ),
  },
  {
    key: 'lastLogin',
    title: 'Last Login',
    sortable: true,
    render: (user: User) => (
      <span className="text-sm text-gray-500">
        {formatDate(user.lastLogin)}
      </span>
    ),
  },
  {
    key: 'actions',
    title: 'Actions',
    width: '120px',
    render: (user: User) => (
      <ActionMenu>
        <ActionMenuItem
          icon={<Eye size="xs" />}
          onClick={() => viewUser(user.id)}
        >
          View
        </ActionMenuItem>
        <ActionMenuItem
          icon={<Edit size="xs" />}
          onClick={() => editUser(user.id)}
        >
          Edit
        </ActionMenuItem>
        <ActionMenuItem
          icon={<Trash2 size="xs" />}
          onClick={() => deleteUser(user.id)}
          variant="danger"
        >
          Delete
        </ActionMenuItem>
      </ActionMenu>
    ),
  },
];
```

### 5.2 Product Inventory Template

#### 5.2.1 Grid View Layout

```typescript
const ProductInventoryTemplate = () => {
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');
  
  return (
    <div className="product-inventory-page">
      <PageHeader>
        <h1>Product Inventory</h1>
        <div className="page-actions">
          <ViewToggle
            value={viewMode}
            onChange={setViewMode}
            options={[
              { value: 'grid', icon: <Grid size="sm" /> },
              { value: 'table', icon: <List size="sm" /> },
            ]}
          />
          <Button variant="outline">
            <Filter size="sm" />
            Filters
          </Button>
          <Button variant="primary">
            <Plus size="sm" />
            Add Product
          </Button>
        </div>
      </PageHeader>
      
      <div className="page-content">
        <div className="inventory-filters">
          <SearchInput
            placeholder="Search products..."
            value={searchQuery}
            onChange={setSearchQuery}
          />
          
          <div className="filter-row">
            <Select
              placeholder="Category"
              options={categoryOptions}
              value={selectedCategory}
              onChange={setSelectedCategory}
            />
            
            <Select
              placeholder="Stock Status"
              options={stockStatusOptions}
              value={selectedStockStatus}
              onChange={setSelectedStockStatus}
            />
            
            <PriceRangeSlider
              min={0}
              max={1000}
              value={priceRange}
              onChange={setPriceRange}
            />
          </div>
        </div>
        
        <div className="inventory-content">
          {viewMode === 'grid' ? (
            <ProductGrid
              products={filteredProducts}
              loading={isLoading}
              onSelect={handleProductSelect}
            />
          ) : (
            <ProductTable
              products={filteredProducts}
              loading={isLoading}
              onSort={handleSort}
              onSelect={handleProductSelect}
            />
          )}
        </div>
        
        <div className="pagination-section">
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
          />
        </div>
      </div>
    </div>
  );
};
```

#### 5.2.2 Product Grid Component

```typescript
const ProductGrid = ({ products, loading, onSelect }: ProductGridProps) => {
  return (
    <div className="product-grid">
      {loading ? (
        <ProductGridSkeleton />
      ) : (
        products.map((product) => (
          <ProductCard
            key={product.id}
            product={product}
            onClick={() => onSelect(product)}
          />
        ))
      )}
    </div>
  );
};

const ProductCard = ({ product, onClick }: ProductCardProps) => {
  return (
    <Card
      variant="interactive"
      clickable
      onClick={onClick}
      className="product-card"
    >
      <div className="product-image">
        <img
          src={product.image}
          alt={product.name}
          className="w-full h-48 object-cover"
        />
        <div className="product-badge">
          <StockBadge stock={product.stock} />
        </div>
      </div>
      
      <CardContent>
        <h3 className="product-name">{product.name}</h3>
        <p className="product-description">{product.description}</p>
        
        <div className="product-details">
          <span className="product-price">${product.price}</span>
          <span className="product-stock">
            Stock: {product.stock}
          </span>
        </div>
        
        <div className="product-actions">
          <Button
            size="sm"
            variant="outline"
            onClick={(e) => {
              e.stopPropagation();
              editProduct(product.id);
            }}
          >
            <Edit size="xs" />
            Edit
          </Button>
          
          <Button
            size="sm"
            variant="outline"
            onClick={(e) => {
              e.stopPropagation();
              viewProduct(product.id);
            }}
          >
            <Eye size="xs" />
            View
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
```

## 6. Detail/Form View Templates

### 6.1 User Profile Template

#### 6.1.1 Profile Layout

```typescript
const UserProfileTemplate = () => {
  const [activeTab, setActiveTab] = useState('profile');
  
  return (
    <div className="user-profile-page">
      <div className="profile-header">
        <div className="profile-banner">
          <img
            src={user.banner}
            alt="Profile banner"
            className="banner-image"
          />
        </div>
        
        <div className="profile-info">
          <div className="profile-avatar">
            <Avatar
              src={user.avatar}
              name={user.name}
              size="xl"
            />
            <Button
              variant="outline"
              size="sm"
              className="change-avatar-btn"
            >
              <Camera size="xs" />
              Change Photo
            </Button>
          </div>
          
          <div className="profile-details">
            <h1 className="profile-name">{user.name}</h1>
            <p className="profile-title">{user.title}</p>
            <p className="profile-department">{user.department}</p>
            
            <div className="profile-meta">
              <span className="profile-meta-item">
                <Mail size="sm" />
                {user.email}
              </span>
              <span className="profile-meta-item">
                <Phone size="sm" />
                {user.phone}
              </span>
              <span className="profile-meta-item">
                <MapPin size="sm" />
                {user.location}
              </span>
            </div>
          </div>
          
          <div className="profile-actions">
            <Button variant="outline">
              <MessageSquare size="sm" />
              Message
            </Button>
            <Button variant="primary">
              <Edit size="sm" />
              Edit Profile
            </Button>
          </div>
        </div>
      </div>
      
      <div className="profile-content">
        <div className="profile-tabs">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger value="profile">Profile</TabsTrigger>
              <TabsTrigger value="activity">Activity</TabsTrigger>
              <TabsTrigger value="settings">Settings</TabsTrigger>
              <TabsTrigger value="security">Security</TabsTrigger>
            </TabsList>
            
            <TabsContent value="profile">
              <ProfileDetailsTab user={user} />
            </TabsContent>
            
            <TabsContent value="activity">
              <ActivityTab userId={user.id} />
            </TabsContent>
            
            <TabsContent value="settings">
              <SettingsTab user={user} />
            </TabsContent>
            
            <TabsContent value="security">
              <SecurityTab user={user} />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};
```

#### 6.1.2 Profile Details Tab

```typescript
const ProfileDetailsTab = ({ user }: { user: User }) => {
  return (
    <div className="profile-details-tab">
      <div className="profile-grid">
        <div className="profile-main">
          <Card>
            <CardHeader>
              <h3>Personal Information</h3>
              <Button variant="ghost" size="sm">
                <Edit size="xs" />
                Edit
              </Button>
            </CardHeader>
            <CardContent>
              <div className="info-grid">
                <InfoItem label="Full Name" value={user.name} />
                <InfoItem label="Email" value={user.email} />
                <InfoItem label="Phone" value={user.phone} />
                <InfoItem label="Date of Birth" value={user.dateOfBirth} />
                <InfoItem label="Location" value={user.location} />
                <InfoItem label="Time Zone" value={user.timeZone} />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <h3>Professional Information</h3>
              <Button variant="ghost" size="sm">
                <Edit size="xs" />
                Edit
              </Button>
            </CardHeader>
            <CardContent>
              <div className="info-grid">
                <InfoItem label="Job Title" value={user.title} />
                <InfoItem label="Department" value={user.department} />
                <InfoItem label="Manager" value={user.manager} />
                <InfoItem label="Start Date" value={user.startDate} />
                <InfoItem label="Employee ID" value={user.employeeId} />
              </div>
            </CardContent>
          </Card>
        </div>
        
        <div className="profile-sidebar">
          <Card>
            <CardHeader>
              <h3>Quick Stats</h3>
            </CardHeader>
            <CardContent>
              <div className="stats-grid">
                <StatItem
                  label="Projects"
                  value={user.stats.projects}
                  icon={<Folder size="sm" />}
                />
                <StatItem
                  label="Tasks Completed"
                  value={user.stats.tasksCompleted}
                  icon={<CheckCircle size="sm" />}
                />
                <StatItem
                  label="Hours Logged"
                  value={user.stats.hoursLogged}
                  icon={<Clock size="sm" />}
                />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <h3>Recent Activity</h3>
            </CardHeader>
            <CardContent>
              <RecentActivityList userId={user.id} limit={5} />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
```

### 6.2 Product Details Template

#### 6.2.1 Product Detail Layout

```typescript
const ProductDetailsTemplate = () => {
  const [activeTab, setActiveTab] = useState('overview');
  
  return (
    <div className="product-details-page">
      <div className="product-header">
        <Breadcrumb>
          <BreadcrumbItem href="/products">Products</BreadcrumbItem>
          <BreadcrumbItem href="/products/category">Electronics</BreadcrumbItem>
          <BreadcrumbItem>{product.name}</BreadcrumbItem>
        </Breadcrumb>
        
        <div className="product-actions">
          <Button variant="outline">
            <Share size="sm" />
            Share
          </Button>
          <Button variant="outline">
            <Edit size="sm" />
            Edit
          </Button>
          <Button variant="primary">
            <ShoppingCart size="sm" />
            Add to Cart
          </Button>
        </div>
      </div>
      
      <div className="product-content">
        <div className="product-main">
          <div className="product-images">
            <ProductImageGallery images={product.images} />
          </div>
          
          <div className="product-info">
            <div className="product-basic-info">
              <h1 className="product-title">{product.name}</h1>
              <p className="product-description">{product.description}</p>
              
              <div className="product-meta">
                <span className="product-price">${product.price}</span>
                <span className="product-sku">SKU: {product.sku}</span>
                <StockBadge stock={product.stock} />
              </div>
              
              <div className="product-tags">
                {product.tags.map(tag => (
                  <Badge key={tag} variant="secondary">{tag}</Badge>
                ))}
              </div>
            </div>
            
            <div className="product-actions">
              <QuantitySelector
                value={quantity}
                onChange={setQuantity}
                max={product.stock}
              />
              
              <div className="action-buttons">
                <Button variant="primary" size="lg">
                  Add to Cart
                </Button>
                <Button variant="outline" size="lg">
                  <Heart size="sm" />
                  Wishlist
                </Button>
              </div>
            </div>
          </div>
        </div>
        
        <div className="product-details">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="specifications">Specifications</TabsTrigger>
              <TabsTrigger value="reviews">Reviews</TabsTrigger>
              <TabsTrigger value="inventory">Inventory</TabsTrigger>
            </TabsList>
            
            <TabsContent value="overview">
              <ProductOverviewTab product={product} />
            </TabsContent>
            
            <TabsContent value="specifications">
              <ProductSpecificationsTab product={product} />
            </TabsContent>
            
            <TabsContent value="reviews">
              <ProductReviewsTab productId={product.id} />
            </TabsContent>
            
            <TabsContent value="inventory">
              <ProductInventoryTab product={product} />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};
```

## 7. Settings Templates

### 7.1 Application Settings Template

#### 7.1.1 Settings Layout

```typescript
const SettingsTemplate = () => {
  const [activeSection, setActiveSection] = useState('general');
  
  return (
    <div className="settings-page">
      <div className="settings-header">
        <h1>Settings</h1>
        <div className="settings-actions">
          <Button variant="outline">
            <RotateCcw size="sm" />
            Reset to Defaults
          </Button>
          <Button variant="primary">
            <Save size="sm" />
            Save Changes
          </Button>
        </div>
      </div>
      
      <div className="settings-content">
        <div className="settings-sidebar">
          <SettingsNavigation
            activeSection={activeSection}
            onSectionChange={setActiveSection}
          />
        </div>
        
        <div className="settings-main">
          <SettingsContent activeSection={activeSection} />
        </div>
      </div>
    </div>
  );
};
```

#### 7.1.2 Settings Navigation

```typescript
const SettingsNavigation = ({ activeSection, onSectionChange }: SettingsNavigationProps) => {
  const settingsSections = [
    {
      id: 'general',
      label: 'General',
      icon: <Settings size="sm" />,
      description: 'Basic application settings',
    },
    {
      id: 'appearance',
      label: 'Appearance',
      icon: <Palette size="sm" />,
      description: 'Theme and display preferences',
    },
    {
      id: 'notifications',
      label: 'Notifications',
      icon: <Bell size="sm" />,
      description: 'Email and push notification settings',
    },
    {
      id: 'security',
      label: 'Security',
      icon: <Shield size="sm" />,
      description: 'Password and security settings',
    },
    {
      id: 'integrations',
      label: 'Integrations',
      icon: <Plug size="sm" />,
      description: 'Third-party integrations',
    },
    {
      id: 'advanced',
      label: 'Advanced',
      icon: <Wrench size="sm" />,
      description: 'Advanced configuration options',
    },
  ];
  
  return (
    <nav className="settings-navigation">
      {settingsSections.map((section) => (
        <button
          key={section.id}
          className={cn(
            'settings-nav-item',
            activeSection === section.id && 'active'
          )}
          onClick={() => onSectionChange(section.id)}
        >
          <div className="nav-item-icon">{section.icon}</div>
          <div className="nav-item-content">
            <div className="nav-item-label">{section.label}</div>
            <div className="nav-item-description">{section.description}</div>
          </div>
        </button>
      ))}
    </nav>
  );
};
```

#### 7.1.3 Settings Content Sections

```typescript
const SettingsContent = ({ activeSection }: { activeSection: string }) => {
  switch (activeSection) {
    case 'general':
      return <GeneralSettings />;
    case 'appearance':
      return <AppearanceSettings />;
    case 'notifications':
      return <NotificationSettings />;
    case 'security':
      return <SecuritySettings />;
    case 'integrations':
      return <IntegrationSettings />;
    case 'advanced':
      return <AdvancedSettings />;
    default:
      return <GeneralSettings />;
  }
};

const GeneralSettings = () => {
  return (
    <div className="settings-section">
      <div className="section-header">
        <h2>General Settings</h2>
        <p>Configure basic application preferences</p>
      </div>
      
      <div className="settings-cards">
        <Card>
          <CardHeader>
            <h3>Organization Information</h3>
          </CardHeader>
          <CardContent>
            <div className="settings-form">
              <FormField label="Organization Name" required>
                <Input defaultValue="ITDO Corporation" />
              </FormField>
              
              <FormField label="Website">
                <Input
                  type="url"
                  defaultValue="https://itdo.co.jp"
                  prefixIcon={<Globe size="sm" />}
                />
              </FormField>
              
              <FormField label="Time Zone">
                <Select
                  defaultValue="Asia/Tokyo"
                  options={timezoneOptions}
                />
              </FormField>
              
              <FormField label="Language">
                <Select
                  defaultValue="en"
                  options={languageOptions}
                />
              </FormField>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <h3>Regional Settings</h3>
          </CardHeader>
          <CardContent>
            <div className="settings-form">
              <FormField label="Currency">
                <Select
                  defaultValue="USD"
                  options={currencyOptions}
                />
              </FormField>
              
              <FormField label="Date Format">
                <Select
                  defaultValue="MM/DD/YYYY"
                  options={dateFormatOptions}
                />
              </FormField>
              
              <FormField label="Number Format">
                <Select
                  defaultValue="1,234.56"
                  options={numberFormatOptions}
                />
              </FormField>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
```

## 8. Responsive Design Patterns

### 8.1 Mobile-First Templates

#### 8.1.1 Mobile Navigation

```typescript
const MobileNavigation = () => {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <div className="mobile-navigation">
      <div className="mobile-header">
        <button
          className="mobile-menu-toggle"
          onClick={() => setIsOpen(!isOpen)}
        >
          <Menu size="md" />
        </button>
        
        <Logo size="sm" />
        
        <div className="mobile-header-actions">
          <Button variant="ghost" size="sm">
            <Search size="sm" />
          </Button>
          <Button variant="ghost" size="sm">
            <Bell size="sm" />
          </Button>
        </div>
      </div>
      
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            className="mobile-menu-overlay"
          >
            <div className="mobile-menu">
              <MobileMenuContent />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
```

#### 8.1.2 Mobile Dashboard

```typescript
const MobileDashboard = () => {
  return (
    <div className="mobile-dashboard">
      <div className="mobile-dashboard-header">
        <h1>Dashboard</h1>
        <Button variant="ghost" size="sm">
          <Filter size="sm" />
        </Button>
      </div>
      
      <div className="mobile-dashboard-content">
        {/* KPI Cards - Horizontal scroll */}
        <div className="kpi-scroll">
          <div className="kpi-cards">
            <KPICard {...kpiData[0]} />
            <KPICard {...kpiData[1]} />
            <KPICard {...kpiData[2]} />
          </div>
        </div>
        
        {/* Main Chart - Full width */}
        <div className="main-chart">
          <Card>
            <CardHeader>
              <h3>Revenue Trend</h3>
            </CardHeader>
            <CardContent>
              <ResponsiveLineChart data={revenueData} />
            </CardContent>
          </Card>
        </div>
        
        {/* Recent Activity - Compact list */}
        <div className="recent-activity">
          <Card>
            <CardHeader>
              <h3>Recent Activity</h3>
            </CardHeader>
            <CardContent>
              <CompactActivityList items={recentActivity} />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
```

### 8.2 Tablet Optimizations

#### 8.2.1 Tablet Layout

```typescript
const TabletLayout = ({ children }: { children: React.ReactNode }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  
  return (
    <div className="tablet-layout">
      <div className="tablet-header">
        <button
          className="sidebar-toggle"
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
        >
          <Menu size="md" />
        </button>
        
        <div className="header-content">
          <Logo />
          <HeaderActions />
        </div>
      </div>
      
      <div className="tablet-content">
        <div className={cn(
          'tablet-sidebar',
          sidebarCollapsed && 'collapsed'
        )}>
          <TabletSidebar collapsed={sidebarCollapsed} />
        </div>
        
        <div className="tablet-main">
          {children}
        </div>
      </div>
    </div>
  );
};
```

## 9. Error and Empty States

### 9.1 Error Page Templates

#### 9.1.1 404 Error Page

```typescript
const NotFoundTemplate = () => {
  return (
    <div className="error-page">
      <div className="error-content">
        <div className="error-illustration">
          <FileText size="xl" color="muted" />
        </div>
        
        <div className="error-text">
          <h1>404</h1>
          <h2>Page Not Found</h2>
          <p>
            The page you're looking for doesn't exist or has been moved.
          </p>
        </div>
        
        <div className="error-actions">
          <Button variant="primary" onClick={() => navigate('/')}>
            <Home size="sm" />
            Go Home
          </Button>
          
          <Button variant="outline" onClick={() => navigate(-1)}>
            <ArrowLeft size="sm" />
            Go Back
          </Button>
        </div>
      </div>
    </div>
  );
};
```

#### 9.1.2 500 Error Page

```typescript
const ServerErrorTemplate = () => {
  return (
    <div className="error-page">
      <div className="error-content">
        <div className="error-illustration">
          <AlertTriangle size="xl" color="error" />
        </div>
        
        <div className="error-text">
          <h1>500</h1>
          <h2>Server Error</h2>
          <p>
            Something went wrong on our end. Please try again later.
          </p>
        </div>
        
        <div className="error-actions">
          <Button variant="primary" onClick={() => window.location.reload()}>
            <Refresh size="sm" />
            Retry
          </Button>
          
          <Button variant="outline" onClick={() => navigate('/')}>
            <Home size="sm" />
            Go Home
          </Button>
        </div>
      </div>
    </div>
  );
};
```

### 9.2 Empty State Templates

#### 9.2.1 Empty List State

```typescript
const EmptyListTemplate = ({ 
  title, 
  description, 
  actionLabel, 
  onAction,
  illustration 
}: EmptyListProps) => {
  return (
    <div className="empty-state">
      <div className="empty-illustration">
        {illustration || <Package size="xl" color="muted" />}
      </div>
      
      <div className="empty-content">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
      
      {onAction && (
        <div className="empty-actions">
          <Button variant="primary" onClick={onAction}>
            <Plus size="sm" />
            {actionLabel}
          </Button>
        </div>
      )}
    </div>
  );
};
```

#### 9.2.2 Empty Search State

```typescript
const EmptySearchTemplate = ({ 
  query, 
  onClear,
  suggestions 
}: EmptySearchProps) => {
  return (
    <div className="empty-search-state">
      <div className="empty-illustration">
        <Search size="xl" color="muted" />
      </div>
      
      <div className="empty-content">
        <h3>No results found</h3>
        <p>
          No results found for "<strong>{query}</strong>". 
          Try adjusting your search terms.
        </p>
      </div>
      
      <div className="empty-actions">
        <Button variant="outline" onClick={onClear}>
          <X size="sm" />
          Clear Search
        </Button>
      </div>
      
      {suggestions && suggestions.length > 0 && (
        <div className="search-suggestions">
          <h4>Try searching for:</h4>
          <div className="suggestion-tags">
            {suggestions.map((suggestion) => (
              <Badge
                key={suggestion}
                variant="secondary"
                className="suggestion-tag"
              >
                {suggestion}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
```

## 10. Implementation Guidelines

### 10.1 Template Usage

#### 10.1.1 Template Selection

```typescript
// Template registry
const PAGE_TEMPLATES = {
  'auth/login': LoginPageTemplate,
  'auth/reset': PasswordResetTemplate,
  'auth/2fa': TwoFactorAuthTemplate,
  'dashboard/overview': DashboardTemplate,
  'dashboard/analytics': AnalyticsDashboardTemplate,
  'users/list': UserManagementTemplate,
  'users/detail': UserProfileTemplate,
  'products/list': ProductInventoryTemplate,
  'products/detail': ProductDetailsTemplate,
  'settings/app': SettingsTemplate,
  'error/404': NotFoundTemplate,
  'error/500': ServerErrorTemplate,
} as const;

// Template resolver
const resolveTemplate = (route: string) => {
  return PAGE_TEMPLATES[route] || NotFoundTemplate;
};
```

#### 10.1.2 Template Customization

```typescript
// Extend base template
const CustomDashboardTemplate = () => {
  return (
    <DashboardTemplate>
      <CustomKPISection />
      <CustomChartSection />
      <CustomActivitySection />
    </DashboardTemplate>
  );
};

// Override template sections
const DashboardWithCustomHeader = () => {
  return (
    <DashboardTemplate
      header={<CustomDashboardHeader />}
      sidebar={<CustomDashboardSidebar />}
    >
      <DefaultDashboardContent />
    </DashboardTemplate>
  );
};
```

### 10.2 Performance Optimization

#### 10.2.1 Template Lazy Loading

```typescript
// Lazy load templates
const LazyDashboard = lazy(() => import('./templates/DashboardTemplate'));
const LazyUserManagement = lazy(() => import('./templates/UserManagementTemplate'));

// Route configuration
const routes = [
  {
    path: '/dashboard',
    component: LazyDashboard,
  },
  {
    path: '/users',
    component: LazyUserManagement,
  },
];
```

#### 10.2.2 Template Caching

```typescript
// Template cache
const templateCache = new Map<string, React.ComponentType>();

const getCachedTemplate = (templateKey: string) => {
  if (!templateCache.has(templateKey)) {
    const Template = PAGE_TEMPLATES[templateKey];
    templateCache.set(templateKey, Template);
  }
  return templateCache.get(templateKey);
};
```

### 10.3 Testing Templates

#### 10.3.1 Template Testing

```typescript
// Template test utilities
const renderTemplate = (Template: React.ComponentType, props = {}) => {
  return render(
    <MemoryRouter>
      <Template {...props} />
    </MemoryRouter>
  );
};

// Template test example
describe('DashboardTemplate', () => {
  it('renders all sections', () => {
    renderTemplate(DashboardTemplate);
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByRole('main')).toBeInTheDocument();
    expect(screen.getByRole('navigation')).toBeInTheDocument();
  });
  
  it('handles responsive behavior', () => {
    // Test responsive behavior
  });
});
```

---

**Document Status**: ✅ Complete and Ready for Implementation  
**Template Count**: 15+ comprehensive page templates  
**Coverage**: Authentication, Dashboard, List/Detail views, Settings, Error states  
**Next Steps**: Begin implementation with priority templates  

---

*This document provides the complete specification for implementing consistent, responsive, and accessible page templates across the ITDO ERP2 system. Templates should be implemented following these specifications to ensure consistency and maintainability.*