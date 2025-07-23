import React, { useState, FormEvent } from "react";
import { cn } from "@/lib/utils";

export interface LinkSection {
  id: string;
  title: string;
  links: {
    id: string;
    label: string;
    href?: string;
    onClick?: (e: React.MouseEvent) => void;
  }[];
}

export interface SocialLink {
  id: string;
  platform: string;
  href: string;
  icon?: React.ReactNode;
}

export interface LegalLink {
  id: string;
  label: string;
  href: string;
}

export interface ContactInfo {
  address?: string;
  phone?: string;
  email?: string;
}

export interface Certification {
  id: string;
  name: string;
  icon?: React.ReactNode;
  description?: string;
}

export interface Award {
  id: string;
  title: string;
  organization: string;
}

export interface AppStoreLink {
  platform: "ios" | "android";
  href: string;
  image: string;
}

export interface PaymentMethod {
  id: string;
  name: string;
  icon?: React.ReactNode;
}

export interface SecurityBadge {
  id: string;
  name: string;
  icon?: React.ReactNode;
}

export interface Language {
  code: string;
  label: string;
}

export interface FooterProps {
  companyName?: string;
  companyDescription?: string;
  logo?: React.ReactNode;
  linkSections?: LinkSection[];
  socialLinks?: SocialLink[];
  legalLinks?: LegalLink[];
  contactInfo?: ContactInfo;
  certifications?: Certification[];
  awards?: Award[];
  appStoreLinks?: AppStoreLink[];
  paymentMethods?: PaymentMethod[];
  securityBadges?: SecurityBadge[];
  languages?: Language[];
  currentLanguage?: string;
  copyright?: string;
  customContent?: React.ReactNode;
  variant?: "default" | "minimal" | "expanded";
  theme?: "light" | "dark";
  sticky?: boolean;
  fullWidth?: boolean;
  showBorder?: boolean;
  centered?: boolean;
  responsive?: boolean;
  showNewsletter?: boolean;
  showBackToTop?: boolean;
  loading?: boolean;
  loadingComponent?: React.ReactNode;
  onNewsletterSignup?: (email: string) => void;
  onBackToTop?: () => void;
  onLanguageChange?: (langCode: string) => void;
  className?: string;
  "data-testid"?: string;
  "data-category"?: string;
  "data-id"?: string;
}

export const Footer: React.FC<FooterProps> = ({
  companyName,
  companyDescription,
  logo,
  linkSections = [],
  socialLinks = [],
  legalLinks = [],
  contactInfo,
  certifications = [],
  awards = [],
  appStoreLinks = [],
  paymentMethods = [],
  securityBadges = [],
  languages = [],
  currentLanguage,
  copyright,
  customContent,
  variant = "default",
  theme = "light",
  sticky = false,
  fullWidth = true,
  showBorder = true,
  centered = false,
  responsive = true,
  showNewsletter = false,
  showBackToTop = false,
  loading = false,
  loadingComponent,
  onNewsletterSignup,
  onBackToTop,
  onLanguageChange,
  className,
  "data-testid": dataTestId = "footer-container",
  "data-category": dataCategory,
  "data-id": dataId,
  ...props
}) => {
  const [newsletterEmail, setNewsletterEmail] = useState("");
  const [languageMenuOpen, setLanguageMenuOpen] = useState(false);

  const variantClasses = {
    default: "py-12",
    minimal: "py-6",
    expanded: "py-16",
  };

  const themeClasses = {
    light: "bg-gray-50 text-gray-900",
    dark: "bg-gray-900 text-white",
  };

  const handleNewsletterSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (newsletterEmail && onNewsletterSignup) {
      onNewsletterSignup(newsletterEmail);
      setNewsletterEmail("");
    }
  };

  const generateCopyright = () => {
    if (copyright) return copyright;
    if (companyName) {
      const currentYear = new Date().getFullYear();
      return `© ${currentYear} ${companyName}. All rights reserved.`;
    }
    return "";
  };

  if (loading) {
    return (
      <footer
        data-testid="footer-loading"
        className={cn(
          "flex items-center justify-center py-8",
          themeClasses[theme],
          showBorder && "border-t",
          className,
        )}
      >
        {loadingComponent || (
          <div className="flex items-center space-x-2">
            <div className="w-5 h-5 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
            <span className="text-gray-500">Loading...</span>
          </div>
        )}
      </footer>
    );
  }

  return (
    <footer
      className={cn(
        "relative",
        variantClasses[variant],
        themeClasses[theme],
        `theme-${theme}`,
        sticky && "sticky bottom-0 z-40",
        fullWidth && "w-full",
        showBorder && "border-t",
        centered && "text-center",
        responsive && "responsive-footer",
        className,
      )}
      data-testid={dataTestId}
      data-category={dataCategory}
      data-id={dataId}
      {...props}
    >
      <div className={cn("mx-auto px-6", !fullWidth && "max-w-7xl")}>
        {/* Main Footer Content */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-8">
          {/* Company Section */}
          {(companyName ||
            companyDescription ||
            logo ||
            socialLinks.length > 0 ||
            appStoreLinks.length > 0) && (
            <div className="col-span-1 lg:col-span-2">
              {logo && <div className="mb-4">{logo}</div>}
              {companyName && (
                <h3 className="text-lg font-semibold mb-2">{companyName}</h3>
              )}
              {companyDescription && (
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {companyDescription}
                </p>
              )}

              {/* Social Links */}
              {socialLinks.length > 0 && (
                <div className="flex space-x-4 mb-4">
                  {socialLinks.map((social) => (
                    <a
                      key={social.id}
                      href={social.href}
                      className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {social.icon}
                    </a>
                  ))}
                </div>
              )}

              {/* App Store Links */}
              {appStoreLinks.length > 0 && (
                <div className="flex space-x-3">
                  {appStoreLinks.map((app) => (
                    <a
                      key={app.platform}
                      href={app.href}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <img
                        src={app.image}
                        alt={
                          app.platform === "ios"
                            ? "Download on the App Store"
                            : "Get it on Google Play"
                        }
                        className="h-10"
                      />
                    </a>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Link Sections */}
          {linkSections.map((section) => (
            <div key={section.id}>
              <h4 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                {section.title}
              </h4>
              <ul className="space-y-2">
                {section.links.map((link) => (
                  <li key={link.id}>
                    {link.href ? (
                      <a
                        href={link.href}
                        className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors"
                        onClick={link.onClick}
                      >
                        {link.label}
                      </a>
                    ) : (
                      <button
                        onClick={link.onClick}
                        className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors text-left"
                      >
                        {link.label}
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}

          {/* Contact Information */}
          {contactInfo && (
            <div>
              <h4 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                Contact
              </h4>
              <div className="space-y-2">
                {contactInfo.address && (
                  <p className="text-gray-600 dark:text-gray-400">
                    {contactInfo.address}
                  </p>
                )}
                {contactInfo.phone && (
                  <p className="text-gray-600 dark:text-gray-400">
                    {contactInfo.phone}
                  </p>
                )}
                {contactInfo.email && (
                  <p className="text-gray-600 dark:text-gray-400">
                    {contactInfo.email}
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Newsletter Signup */}
        {showNewsletter && (
          <div className="mb-8 p-6 bg-gray-100 dark:bg-gray-800 rounded-lg">
            <h4 className="text-lg font-semibold mb-2">
              Subscribe to our newsletter
            </h4>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Get the latest updates and news delivered to your inbox.
            </p>
            <form onSubmit={handleNewsletterSubmit} className="flex gap-2">
              <input
                type="email"
                value={newsletterEmail}
                onChange={(e) => setNewsletterEmail(e.target.value)}
                placeholder="Enter your email"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                required
              />
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Subscribe
              </button>
            </form>
          </div>
        )}

        {/* Certifications */}
        {certifications.length > 0 && (
          <div className="mb-8">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
              Certifications
            </h4>
            <div className="flex flex-wrap gap-4">
              {certifications.map((cert) => (
                <div key={cert.id} className="flex items-center space-x-2">
                  {cert.icon}
                  <div>
                    <span className="font-medium">{cert.name}</span>
                    {cert.description && (
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {cert.description}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Awards */}
        {awards.length > 0 && (
          <div className="mb-8">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
              Awards & Recognition
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {awards.map((award) => (
                <div key={award.id}>
                  <h5 className="font-medium">{award.title}</h5>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {award.organization}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Payment Methods */}
        {paymentMethods.length > 0 && (
          <div className="mb-8">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
              Payment Methods
            </h4>
            <div className="flex space-x-4">
              {paymentMethods.map((method) => (
                <div key={method.id} className="flex items-center space-x-2">
                  {method.icon}
                  <span className="text-sm">{method.name}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Security Badges */}
        {securityBadges.length > 0 && (
          <div className="mb-8">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
              Security
            </h4>
            <div className="flex space-x-4">
              {securityBadges.map((badge) => (
                <div key={badge.id} className="flex items-center space-x-2">
                  {badge.icon}
                  <span className="text-sm">{badge.name}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Custom Content */}
        {customContent && <div className="mb-8">{customContent}</div>}

        {/* Footer Bottom */}
        <div className="pt-8 border-t border-gray-200 dark:border-gray-700">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            {/* Copyright */}
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {generateCopyright()}
            </div>

            {/* Legal Links */}
            {legalLinks.length > 0 && (
              <div className="flex space-x-6">
                {legalLinks.map((link) => (
                  <a
                    key={link.id}
                    href={link.href}
                    className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors"
                  >
                    {link.label}
                  </a>
                ))}
              </div>
            )}

            {/* Language Selector */}
            {languages.length > 0 && (
              <div className="relative">
                <button
                  data-testid="footer-language-selector"
                  onClick={() => setLanguageMenuOpen(!languageMenuOpen)}
                  className="flex items-center space-x-1 text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors"
                >
                  <span>
                    {languages.find((lang) => lang.code === currentLanguage)
                      ?.label || "Language"}
                  </span>
                  <span>▼</span>
                </button>

                {languageMenuOpen && (
                  <div className="absolute bottom-full right-0 mb-2 w-32 bg-white dark:bg-gray-800 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-50">
                    {languages.map((lang) => (
                      <button
                        key={lang.code}
                        onClick={() => {
                          onLanguageChange?.(lang.code);
                          setLanguageMenuOpen(false);
                        }}
                        className={cn(
                          "block w-full text-left px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors",
                          lang.code === currentLanguage
                            ? "text-blue-600 bg-blue-50 dark:bg-blue-900"
                            : "text-gray-700 dark:text-gray-300",
                        )}
                      >
                        {lang.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Back to Top Button */}
      {showBackToTop && (
        <button
          data-testid="back-to-top"
          onClick={onBackToTop}
          className="absolute bottom-4 right-4 bg-blue-600 text-white p-3 rounded-full shadow-lg hover:bg-blue-700 transition-colors"
        >
          ↑
        </button>
      )}
    </footer>
  );
};

export default Footer;
