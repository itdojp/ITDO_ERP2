/**
 * E2Eテスト安定化ヘルパー
 */
import { Page, Locator } from '@playwright/test';

export class StabilityHelper {
  constructor(private page: Page) {}

  /**
   * 要素が安定するまで待機
   */
  async waitForStability(locator: Locator, timeout = 30000) {
    // 要素が表示されるまで待機
    await locator.waitFor({ state: 'visible', timeout });

    // アニメーション完了待機
    await this.page.waitForTimeout(500);

    // ネットワークアイドル待機
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * リトライ付きクリック
   */
  async clickWithRetry(locator: Locator, retries = 3) {
    for (let i = 0; i < retries; i++) {
      try {
        await this.waitForStability(locator);
        await locator.click();
        return;
      } catch (error) {
        if (i === retries - 1) throw error;
        await this.page.waitForTimeout(1000);
      }
    }
  }

  /**
   * API呼び出し完了待機
   */
  async waitForAPI(path: string) {
    await this.page.waitForResponse(
      resp => resp.url().includes(path) && resp.status() === 200
    );
  }

  /**
   * フォーム送信の安定化
   */
  async submitFormWithRetry(formLocator: Locator, submitButton: Locator, retries = 3) {
    for (let i = 0; i < retries; i++) {
      try {
        await this.waitForStability(formLocator);
        await this.clickWithRetry(submitButton);
        
        // 送信完了を待機
        await this.page.waitForTimeout(1000);
        return;
      } catch (error) {
        if (i === retries - 1) throw error;
        await this.page.waitForTimeout(2000);
      }
    }
  }

  /**
   * データローディング完了待機
   */
  async waitForDataLoad(dataContainer: Locator, minimumItems = 1) {
    await this.page.waitForFunction(
      (selector, minItems) => {
        const container = document.querySelector(selector);
        return container && container.children.length >= minItems;
      },
      dataContainer.toString(),
      minimumItems,
      { timeout: 30000 }
    );
  }
}