import { Page } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Login Page Object
 */
export class LoginPage extends BasePage {
  // Element selectors
  private readonly selectors = {
    form: '[data-testid="login-form"]',
    emailInput: '[data-testid="email-input"]',
    passwordInput: '[data-testid="password-input"]',
    loginButton: '[data-testid="login-button"]',
    rememberMe: '[data-testid="remember-me"]',
    forgotPasswordLink: '[data-testid="forgot-password-link"]',
    errorMessage: '[data-testid="login-error"]',
    emailError: '[data-testid="email-error"]',
    passwordError: '[data-testid="password-error"]'
  };

  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to login page
   */
  async gotoLoginPage(): Promise<void> {
    await this.goto('/login');
    await this.waitForElement(this.selectors.form);
  }

  /**
   * Fill login form
   */
  async fillLoginForm(email: string, password: string): Promise<void> {
    await this.fill(this.selectors.emailInput, email);
    await this.fill(this.selectors.passwordInput, password);
  }

  /**
   * Submit login form
   */
  async submitLogin(): Promise<void> {
    await this.click(this.selectors.loginButton);
  }

  /**
   * Complete login process
   */
  async login(email: string, password: string): Promise<void> {
    await this.fillLoginForm(email, password);
    await this.submitLogin();
  }

  /**
   * Check remember me checkbox
   */
  async checkRememberMe(): Promise<void> {
    await this.page.check(this.selectors.rememberMe);
  }

  /**
   * Click forgot password link
   */
  async clickForgotPassword(): Promise<void> {
    await this.click(this.selectors.forgotPasswordLink);
  }

  /**
   * Get error message text
   */
  async getErrorMessage(): Promise<string> {
    return await this.getText(this.selectors.errorMessage);
  }

  /**
   * Get email validation error
   */
  async getEmailError(): Promise<string> {
    return await this.getText(this.selectors.emailError);
  }

  /**
   * Get password validation error
   */
  async getPasswordError(): Promise<string> {
    return await this.getText(this.selectors.passwordError);
  }

  /**
   * Check if login form is visible
   */
  async isLoginFormVisible(): Promise<boolean> {
    return await this.isVisible(this.selectors.form);
  }

  /**
   * Check if error message is displayed
   */
  async hasError(): Promise<boolean> {
    return await this.isVisible(this.selectors.errorMessage);
  }
}