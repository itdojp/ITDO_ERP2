import { Page } from '@playwright/test';

export class LoginPage {
  constructor(private page: Page) {}

  // Locators
  private emailInput = 'input[name="email"]';
  private passwordInput = 'input[name="password"]';
  private submitButton = 'button[type="submit"]';
  private errorMessage = '.error-message';
  private loadingSpinner = '.loading-spinner';

  // Actions
  async goto() {
    await this.page.goto('/login');
  }

  async fillEmail(email: string) {
    await this.page.fill(this.emailInput, email);
  }

  async fillPassword(password: string) {
    await this.page.fill(this.passwordInput, password);
  }

  async submit() {
    await this.page.click(this.submitButton);
  }

  async login(email: string, password: string) {
    await this.fillEmail(email);
    await this.fillPassword(password);
    await this.submit();
  }

  async waitForError() {
    await this.page.waitForSelector(this.errorMessage);
  }

  async getErrorText() {
    return await this.page.textContent(this.errorMessage);
  }

  async isLoading() {
    return await this.page.isVisible(this.loadingSpinner);
  }
}