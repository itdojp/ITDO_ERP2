import { Page, Locator, expect } from '@playwright/test';

export class DashboardPage {
  private page: Page;
  readonly welcomeMessage: Locator;
  readonly userMenu: Locator;
  readonly logoutButton: Locator;
  readonly navigationMenu: Locator;
  readonly statsCards: Locator;

  constructor(page: Page) {
    this.page = page;
    this.welcomeMessage = page.locator('[data-testid="welcome-message"]');
    this.userMenu = page.locator('[data-testid="user-menu"]');
    this.logoutButton = page.locator('button[data-testid="logout-button"]');
    this.navigationMenu = page.locator('nav[data-testid="navigation-menu"]');
    this.statsCards = page.locator('[data-testid="stats-card"]');
  }

  async waitForDashboard() {
    await expect(this.welcomeMessage).toBeVisible();
    await expect(this.navigationMenu).toBeVisible();
  }

  async logout() {
    await this.userMenu.click();
    await this.logoutButton.click();
  }

  async getStatsCount() {
    return await this.statsCards.count();
  }

  async navigateToSection(section: string) {
    await this.page.click(`nav a[href="/${section}"]`);
  }
}