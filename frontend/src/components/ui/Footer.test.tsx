import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { Footer } from './Footer';

describe('Footer', () => {
  const mockLinkSections = [
    {
      id: '1',
      title: 'Company',
      links: [
        { id: '1-1', label: 'About Us', href: '/about' },
        { id: '1-2', label: 'Careers', href: '/careers' },
        { id: '1-3', label: 'Contact', href: '/contact' },
      ]
    },
    {
      id: '2',
      title: 'Products',
      links: [
        { id: '2-1', label: 'Features', href: '/features' },
        { id: '2-2', label: 'Pricing', href: '/pricing' },
        { id: '2-3', label: 'API', href: '/api' },
      ]
    }
  ];

  const mockSocialLinks = [
    { id: '1', platform: 'twitter', href: 'https://twitter.com/company', icon: '🐦' },
    { id: '2', platform: 'facebook', href: 'https://facebook.com/company', icon: '📘' },
    { id: '3', platform: 'linkedin', href: 'https://linkedin.com/company', icon: '💼' },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders footer with company info', () => {
    render(
      <Footer 
        companyName="Acme Corp" 
        companyDescription="Building amazing products since 2020"
      />
    );
    
    expect(screen.getByText('Acme Corp')).toBeInTheDocument();
    expect(screen.getByText('Building amazing products since 2020')).toBeInTheDocument();
  });

  it('renders link sections', () => {
    render(<Footer linkSections={mockLinkSections} />);
    
    expect(screen.getByText('Company')).toBeInTheDocument();
    expect(screen.getByText('Products')).toBeInTheDocument();
    expect(screen.getByText('About Us')).toBeInTheDocument();
    expect(screen.getByText('Features')).toBeInTheDocument();
  });

  it('renders social media links', () => {
    render(<Footer socialLinks={mockSocialLinks} />);
    
    expect(screen.getByText('🐦')).toBeInTheDocument();
    expect(screen.getByText('📘')).toBeInTheDocument();
    expect(screen.getByText('💼')).toBeInTheDocument();
  });

  it('renders copyright notice', () => {
    render(<Footer copyright="© 2023 Acme Corp. All rights reserved." />);
    
    expect(screen.getByText('© 2023 Acme Corp. All rights reserved.')).toBeInTheDocument();
  });

  it('auto-generates copyright with current year', () => {
    const currentYear = new Date().getFullYear();
    render(<Footer companyName="Acme Corp" />);
    
    expect(screen.getByText(`© ${currentYear} Acme Corp. All rights reserved.`)).toBeInTheDocument();
  });

  it('renders logo', () => {
    const logo = <img data-testid="footer-logo" src="/logo.png" alt="Company Logo" />;
    render(<Footer logo={logo} />);
    
    expect(screen.getByTestId('footer-logo')).toBeInTheDocument();
  });

  it('supports different variants', () => {
    const variants = ['default', 'minimal', 'expanded'] as const;
    
    variants.forEach(variant => {
      const { unmount } = render(<Footer companyName="Test" variant={variant} />);
      expect(screen.getByTestId('footer-container')).toBeInTheDocument();
      unmount();
    });
  });

  it('supports different themes', () => {
    const themes = ['light', 'dark'] as const;
    
    themes.forEach(theme => {
      const { unmount } = render(<Footer companyName="Test" theme={theme} />);
      const footer = screen.getByTestId('footer-container');
      expect(footer).toHaveClass(`theme-${theme}`);
      unmount();
    });
  });

  it('renders newsletter signup', () => {
    const onNewsletterSignup = vi.fn();
    render(<Footer showNewsletter onNewsletterSignup={onNewsletterSignup} />);
    
    expect(screen.getByText('Subscribe to our newsletter')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter your email')).toBeInTheDocument();
    
    const emailInput = screen.getByPlaceholderText('Enter your email');
    const submitButton = screen.getByText('Subscribe');
    
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(submitButton);
    
    expect(onNewsletterSignup).toHaveBeenCalledWith('test@example.com');
  });

  it('renders contact information', () => {
    const contactInfo = {
      address: '123 Main St, City, State 12345',
      phone: '+1 (555) 123-4567',
      email: 'contact@company.com'
    };
    
    render(<Footer contactInfo={contactInfo} />);
    
    expect(screen.getByText('123 Main St, City, State 12345')).toBeInTheDocument();
    expect(screen.getByText('+1 (555) 123-4567')).toBeInTheDocument();
    expect(screen.getByText('contact@company.com')).toBeInTheDocument();
  });

  it('supports sticky footer', () => {
    render(<Footer companyName="Test" sticky />);
    
    const footer = screen.getByTestId('footer-container');
    expect(footer).toHaveClass('sticky');
  });

  it('supports full width', () => {
    render(<Footer companyName="Test" fullWidth />);
    
    const footer = screen.getByTestId('footer-container');
    expect(footer).toHaveClass('w-full');
  });

  it('renders with border', () => {
    render(<Footer companyName="Test" showBorder />);
    
    const footer = screen.getByTestId('footer-container');
    expect(footer).toHaveClass('border-t');
  });

  it('supports centered layout', () => {
    render(<Footer companyName="Test" centered />);
    
    const footer = screen.getByTestId('footer-container');
    expect(footer).toHaveClass('text-center');
  });

  it('renders legal links', () => {
    const legalLinks = [
      { id: '1', label: 'Privacy Policy', href: '/privacy' },
      { id: '2', label: 'Terms of Service', href: '/terms' },
      { id: '3', label: 'Cookie Policy', href: '/cookies' },
    ];
    
    render(<Footer legalLinks={legalLinks} />);
    
    expect(screen.getByText('Privacy Policy')).toBeInTheDocument();
    expect(screen.getByText('Terms of Service')).toBeInTheDocument();
    expect(screen.getByText('Cookie Policy')).toBeInTheDocument();
  });

  it('supports custom footer content', () => {
    const customContent = <div data-testid="custom-footer">Custom Footer Content</div>;
    render(<Footer customContent={customContent} />);
    
    expect(screen.getByTestId('custom-footer')).toBeInTheDocument();
  });

  it('renders language selector', () => {
    const languages = [
      { code: 'en', label: 'English' },
      { code: 'es', label: 'Español' },
    ];
    
    const onLanguageChange = vi.fn();
    render(<Footer languages={languages} currentLanguage="en" onLanguageChange={onLanguageChange} />);
    
    const languageSelector = screen.getByTestId('footer-language-selector');
    expect(languageSelector).toBeInTheDocument();
  });

  it('supports loading state', () => {
    render(<Footer companyName="Test" loading />);
    
    expect(screen.getByTestId('footer-loading')).toBeInTheDocument();
  });

  it('supports custom loading component', () => {
    const LoadingComponent = () => <div data-testid="custom-loading">Loading footer...</div>;
    render(<Footer companyName="Test" loading loadingComponent={<LoadingComponent />} />);
    
    expect(screen.getByTestId('custom-loading')).toBeInTheDocument();
  });

  it('renders company certifications', () => {
    const certifications = [
      { id: '1', name: 'ISO 9001', icon: '🏆', description: 'Quality Management' },
      { id: '2', name: 'SOC 2', icon: '🛡️', description: 'Security Compliance' },
    ];
    
    render(<Footer certifications={certifications} />);
    
    expect(screen.getByText('ISO 9001')).toBeInTheDocument();
    expect(screen.getByText('SOC 2')).toBeInTheDocument();
  });

  it('renders awards and recognitions', () => {
    const awards = [
      { id: '1', title: 'Best Product 2023', organization: 'Tech Awards' },
      { id: '2', title: 'Innovation Award', organization: 'Industry Leaders' },
    ];
    
    render(<Footer awards={awards} />);
    
    expect(screen.getByText('Best Product 2023')).toBeInTheDocument();
    expect(screen.getByText('Innovation Award')).toBeInTheDocument();
  });

  it('supports back to top button', () => {
    const onBackToTop = vi.fn();
    render(<Footer showBackToTop onBackToTop={onBackToTop} />);
    
    const backToTopButton = screen.getByTestId('back-to-top');
    expect(backToTopButton).toBeInTheDocument();
    
    fireEvent.click(backToTopButton);
    expect(onBackToTop).toHaveBeenCalledTimes(1);
  });

  it('renders app store badges', () => {
    const appStoreLinks = [
      { platform: 'ios', href: 'https://apps.apple.com/app', image: '/app-store.png' },
      { platform: 'android', href: 'https://play.google.com/store/apps', image: '/google-play.png' },
    ];
    
    render(<Footer appStoreLinks={appStoreLinks} />);
    
    expect(screen.getByAltText('Download on the App Store')).toBeInTheDocument();
    expect(screen.getByAltText('Get it on Google Play')).toBeInTheDocument();
  });

  it('supports custom className', () => {
    render(<Footer companyName="Test" className="custom-footer" />);
    
    expect(screen.getByTestId('footer-container')).toHaveClass('custom-footer');
  });

  it('handles link clicks', () => {
    const onClick = vi.fn();
    const linksWithClick = [
      {
        id: '1',
        title: 'Support',
        links: [
          { id: '1-1', label: 'Help Center', onClick },
        ]
      }
    ];
    
    render(<Footer linkSections={linksWithClick} />);
    
    const helpLink = screen.getByText('Help Center');
    fireEvent.click(helpLink);
    
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('renders payment methods', () => {
    const paymentMethods = [
      { id: '1', name: 'Visa', icon: '💳' },
      { id: '2', name: 'PayPal', icon: '💰' },
    ];
    
    render(<Footer paymentMethods={paymentMethods} />);
    
    expect(screen.getByText('💳')).toBeInTheDocument();
    expect(screen.getByText('💰')).toBeInTheDocument();
  });

  it('supports responsive behavior', () => {
    render(<Footer companyName="Test" responsive />);
    
    const footer = screen.getByTestId('footer-container');
    expect(footer).toHaveClass('responsive-footer');
  });

  it('supports custom data attributes', () => {
    render(<Footer companyName="Test" data-category="site-footer" data-id="main-footer" />);
    
    const footer = screen.getByTestId('footer-container');
    expect(footer).toHaveAttribute('data-category', 'site-footer');
    expect(footer).toHaveAttribute('data-id', 'main-footer');
  });

  it('renders security badges', () => {
    const securityBadges = [
      { id: '1', name: 'SSL Secured', icon: '🔒' },
      { id: '2', name: 'GDPR Compliant', icon: '🛡️' },
    ];
    
    render(<Footer securityBadges={securityBadges} />);
    
    expect(screen.getByText('SSL Secured')).toBeInTheDocument();
    expect(screen.getByText('GDPR Compliant')).toBeInTheDocument();
  });
});