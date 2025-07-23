import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { Header } from './Header';

describe('Header', () => {
  const mockNavItems = [
    { id: '1', label: 'Home', href: '/', current: true },
    { id: '2', label: 'About', href: '/about' },
    { id: '3', label: 'Services', href: '/services' },
  ];

  const mockUserMenu = [
    { id: '1', label: 'Profile', href: '/profile', icon: '👤' },
    { id: '2', label: 'Settings', href: '/settings', icon: '⚙️' },
    { id: '3', label: 'Logout', onClick: vi.fn(), icon: '🚪' },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders header with title', () => {
    render(<Header title="My App" />);
    
    expect(screen.getByText('My App')).toBeInTheDocument();
  });

  it('renders header with logo', () => {
    const logo = <img data-testid="app-logo" src="/logo.png" alt="Logo" />;
    render(<Header logo={logo} />);
    
    expect(screen.getByTestId('app-logo')).toBeInTheDocument();
  });

  it('renders navigation items', () => {
    render(<Header navItems={mockNavItems} />);
    
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('About')).toBeInTheDocument();
    expect(screen.getByText('Services')).toBeInTheDocument();
  });

  it('highlights current navigation item', () => {
    render(<Header navItems={mockNavItems} />);
    
    const homeLink = screen.getByText('Home').closest('a');
    expect(homeLink).toHaveClass('text-blue-600');
  });

  it('renders user menu', () => {
    render(<Header userMenu={mockUserMenu} />);
    
    const userButton = screen.getByTestId('user-menu-button');
    expect(userButton).toBeInTheDocument();
    
    fireEvent.click(userButton);
    
    expect(screen.getByText('Profile')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText('Logout')).toBeInTheDocument();
  });

  it('supports different variants', () => {
    const variants = ['default', 'minimal', 'transparent'] as const;
    
    variants.forEach(variant => {
      const { unmount } = render(<Header title="Test" variant={variant} />);
      expect(screen.getByTestId('header-container')).toBeInTheDocument();
      unmount();
    });
  });

  it('supports different sizes', () => {
    const sizes = ['sm', 'md', 'lg'] as const;
    
    sizes.forEach(size => {
      const { unmount } = render(<Header title="Test" size={size} />);
      expect(screen.getByTestId('header-container')).toBeInTheDocument();
      unmount();
    });
  });

  it('supports sticky header', () => {
    render(<Header title="Test" sticky />);
    
    const header = screen.getByTestId('header-container');
    expect(header).toHaveClass('sticky');
  });

  it('supports fixed header', () => {
    render(<Header title="Test" fixed />);
    
    const header = screen.getByTestId('header-container');
    expect(header).toHaveClass('fixed');
  });

  it('renders search bar', () => {
    const onSearch = vi.fn();
    render(<Header title="Test" showSearch onSearch={onSearch} />);
    
    const searchInput = screen.getByPlaceholderText('Search...');
    expect(searchInput).toBeInTheDocument();
    
    fireEvent.change(searchInput, { target: { value: 'test query' } });
    expect(onSearch).toHaveBeenCalledWith('test query');
  });

  it('supports custom search placeholder', () => {
    render(<Header title="Test" showSearch searchPlaceholder="Find something..." />);
    
    expect(screen.getByPlaceholderText('Find something...')).toBeInTheDocument();
  });

  it('renders breadcrumbs', () => {
    const breadcrumbs = [
      { id: '1', label: 'Home', href: '/' },
      { id: '2', label: 'Category', href: '/category' },
      { id: '3', label: 'Current', current: true },
    ];
    
    render(<Header breadcrumbs={breadcrumbs} />);
    
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Category')).toBeInTheDocument();
    expect(screen.getByText('Current')).toBeInTheDocument();
  });

  it('renders notifications', () => {
    render(<Header showNotifications notificationCount={5} />);
    
    const notificationButton = screen.getByTestId('notification-button');
    expect(notificationButton).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('handles notification click', () => {
    const onNotificationClick = vi.fn();
    render(<Header showNotifications onNotificationClick={onNotificationClick} />);
    
    const notificationButton = screen.getByTestId('notification-button');
    fireEvent.click(notificationButton);
    
    expect(onNotificationClick).toHaveBeenCalledTimes(1);
  });

  it('supports mobile menu toggle', () => {
    render(<Header navItems={mockNavItems} showMobileMenu />);
    
    const mobileToggle = screen.getByTestId('mobile-menu-toggle');
    expect(mobileToggle).toBeInTheDocument();
    
    fireEvent.click(mobileToggle);
    
    // Mobile menu should be visible
    const mobileMenu = screen.getByTestId('mobile-menu');
    expect(mobileMenu).toHaveClass('block');
  });

  it('renders custom actions', () => {
    const actions = (
      <button data-testid="custom-action">Custom Button</button>
    );
    
    render(<Header title="Test" actions={actions} />);
    
    expect(screen.getByTestId('custom-action')).toBeInTheDocument();
  });

  it('supports theme variants', () => {
    const themes = ['light', 'dark'] as const;
    
    themes.forEach(theme => {
      const { unmount } = render(<Header title="Test" theme={theme} />);
      const header = screen.getByTestId('header-container');
      expect(header).toHaveClass(`theme-${theme}`);
      unmount();
    });
  });

  it('renders user avatar', () => {
    render(<Header userAvatar="/avatar.jpg" userName="John Doe" />);
    
    const avatar = screen.getByTestId('user-avatar');
    expect(avatar).toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });

  it('supports center layout', () => {
    render(<Header title="Test" centerContent />);
    
    const header = screen.getByTestId('header-container');
    expect(header).toHaveClass('justify-center');
  });

  it('supports full width', () => {
    render(<Header title="Test" fullWidth />);
    
    const header = screen.getByTestId('header-container');
    expect(header).toHaveClass('w-full');
  });

  it('renders with border', () => {
    render(<Header title="Test" showBorder />);
    
    const header = screen.getByTestId('header-container');
    expect(header).toHaveClass('border-b');
  });

  it('supports shadow', () => {
    render(<Header title="Test" shadow />);
    
    const header = screen.getByTestId('header-container');
    expect(header).toHaveClass('shadow-md');
  });

  it('renders loading state', () => {
    render(<Header title="Test" loading />);
    
    expect(screen.getByTestId('header-loading')).toBeInTheDocument();
  });

  it('supports custom loading component', () => {
    const LoadingComponent = () => <div data-testid="custom-loading">Loading header...</div>;
    render(<Header title="Test" loading loadingComponent={<LoadingComponent />} />);
    
    expect(screen.getByTestId('custom-loading')).toBeInTheDocument();
  });

  it('handles user menu item clicks', () => {
    const mockUserMenuWithClick = [
      { id: '1', label: 'Profile', onClick: vi.fn() },
      { id: '2', label: 'Logout', onClick: vi.fn() },
    ];
    
    render(<Header userMenu={mockUserMenuWithClick} />);
    
    const userButton = screen.getByTestId('user-menu-button');
    fireEvent.click(userButton);
    
    const profileItem = screen.getByText('Profile');
    fireEvent.click(profileItem);
    
    expect(mockUserMenuWithClick[0].onClick).toHaveBeenCalledTimes(1);
  });

  it('supports collapsible navigation', () => {
    render(<Header navItems={mockNavItems} collapsibleNav />);
    
    expect(screen.getByTestId('header-container')).toBeInTheDocument();
  });

  it('renders page title separately', () => {
    render(<Header title="App Name" pageTitle="Current Page" />);
    
    expect(screen.getByText('App Name')).toBeInTheDocument();
    expect(screen.getByText('Current Page')).toBeInTheDocument();
  });

  it('supports custom className', () => {
    render(<Header title="Test" className="custom-header" />);
    
    expect(screen.getByTestId('header-container')).toHaveClass('custom-header');
  });

  it('supports announcement bar', () => {
    render(<Header title="Test" announcement="Important announcement!" />);
    
    expect(screen.getByText('Important announcement!')).toBeInTheDocument();
  });

  it('renders language selector', () => {
    const languages = [
      { code: 'en', label: 'English' },
      { code: 'es', label: 'Español' },
    ];
    
    render(<Header title="Test" languages={languages} currentLanguage="en" />);
    
    const langSelector = screen.getByTestId('language-selector');
    expect(langSelector).toBeInTheDocument();
  });

  it('handles language change', () => {
    const onLanguageChange = vi.fn();
    const languages = [
      { code: 'en', label: 'English' },
      { code: 'es', label: 'Español' },
    ];
    
    render(<Header title="Test" languages={languages} currentLanguage="en" onLanguageChange={onLanguageChange} />);
    
    const langSelector = screen.getByTestId('language-selector');
    fireEvent.click(langSelector);
    
    const spanishOption = screen.getByText('Español');
    fireEvent.click(spanishOption);
    
    expect(onLanguageChange).toHaveBeenCalledWith('es');
  });

  it('supports quick actions', () => {
    const quickActions = [
      { id: '1', label: 'New', icon: '➕', onClick: vi.fn() },
      { id: '2', label: 'Import', icon: '📥', onClick: vi.fn() },
    ];
    
    render(<Header title="Test" quickActions={quickActions} />);
    
    expect(screen.getByText('New')).toBeInTheDocument();
    expect(screen.getByText('Import')).toBeInTheDocument();
  });

  it('supports responsive behavior', () => {
    render(<Header title="Test" responsive />);
    
    const header = screen.getByTestId('header-container');
    expect(header).toHaveClass('responsive-header');
  });

  it('supports custom data attributes', () => {
    render(<Header title="Test" data-category="navigation" data-id="main-header" />);
    
    const header = screen.getByTestId('header-container');
    expect(header).toHaveAttribute('data-category', 'navigation');
    expect(header).toHaveAttribute('data-id', 'main-header');
  });

  it('handles window scroll for fixed header', () => {
    render(<Header title="Test" fixed scrollBehavior />);
    
    const header = screen.getByTestId('header-container');
    
    // Simulate scroll
    fireEvent.scroll(window, { target: { scrollY: 100 } });
    
    expect(header).toBeInTheDocument();
  });
});