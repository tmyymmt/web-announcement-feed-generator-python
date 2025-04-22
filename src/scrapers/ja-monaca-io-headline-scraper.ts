import { By, until, WebElement } from 'selenium-webdriver';
import { BaseScraper } from './base-scraper';
import { Announcement, ScraperResult } from '../types';
import { logger } from '../utils/logger';

export class MonacaHeadlineScraper extends BaseScraper {
  constructor() {
    super('https://ja.monaca.io/headline/');
  }

  async scrape(): Promise<ScraperResult> {
    if (!this.driver) {
      await this.initialize();
    }

    if (!this.driver) {
      throw new Error('Failed to initialize WebDriver');
    }

    try {
      logger.info('Navigating to Monaca headline page');
      await this.driver.get(this.url);

      // ページのロードを待機
      await this.driver.wait(until.elementLocated(By.css('body')), 10000);
      
      // JavaScriptの遅延読み込みのコンテンツが表示されるのを待機
      await this.driver.sleep(3000);

      // お知らせ要素を全て取得
      const headlineEntries = await this.driver.findElements(By.css('.headline-entry'));
      logger.info(`Found ${headlineEntries.length} headline entries`);

      // アナウンスメントのリストを作成
      const announcements: Announcement[] = [];

      for (const entry of headlineEntries) {
        try {
          const announcement = await this.parseHeadlineEntry(entry);
          if (announcement) {
            announcements.push(announcement);
          }
        } catch (error) {
          logger.error(`Error parsing headline entry: ${error}`);
        }
      }

      return {
        announcements,
        source: 'Monaca Headline',
        sourceUrl: this.url,
      };
    } catch (error) {
      logger.error(`Error scraping Monaca headline: ${error}`);
      throw error;
    } finally {
      await this.close();
    }
  }

  private async parseHeadlineEntry(element: WebElement): Promise<Announcement | null> {
    try {
      // お知らせの日付を取得
      const dateElement = await element.findElement(By.css('.headline-entry-date')).catch(() => null);
      if (!dateElement) {
        logger.debug('Headline entry has no date, skipping');
        return null;
      }

      const dateText = await dateElement.getText();
      const date = this.parseJapaneseDate(dateText);

      // お知らせの内容を取得
      const contentElement = await element.findElement(By.css('.headline-entry-content')).catch(() => null);
      if (!contentElement) {
        logger.debug('Headline entry has no content, skipping');
        return null;
      }
      
      const content = await contentElement.getText();

      // お知らせのカテゴリを取得
      const categoryElement = await element.findElement(By.css('.headline-entry-type-badge')).catch(() => null);
      let category = '';
      
      if (categoryElement) {
        category = await categoryElement.getText();
      }
      
      // カテゴリがない場合は内容から推測
      if (!category) {
        const contentLower = content.toLowerCase();
        if (contentLower.includes('deprecated') || contentLower.includes('提供終了') || contentLower.includes('廃止')) {
          category = '提供終了';
        } else if (contentLower.includes('shutdown')) {
          category = '終了';
        } else if (contentLower.includes('important') || contentLower.includes('重要')) {
          category = '重要';
        }
      }

      // リンクがあれば取得
      let link: string | undefined;
      const linkElement = await element.findElement(By.css('a')).catch(() => null);
      if (linkElement) {
        link = await linkElement.getAttribute('href');
      }

      return {
        date,
        content,
        category,
        link,
      };
    } catch (error) {
      logger.error(`Error parsing headline entry element: ${error}`);
      return null;
    }
  }

  private parseJapaneseDate(dateText: string): Date {
    try {
      // 最初に日本語の日付形式（例: 2023年4月1日）を試す
      const regexJP = /(\d{4})年(\d{1,2})月(\d{1,2})日/;
      const matchesJP = dateText.match(regexJP);

      if (matchesJP && matchesJP.length === 4) {
        const year = parseInt(matchesJP[1]);
        const month = parseInt(matchesJP[2]) - 1; // 月は0-11なので1を引く
        const day = parseInt(matchesJP[3]);
        
        return new Date(year, month, day);
      }
      
      // スラッシュ形式の日付（例: 2023/04/01 または 2023/4/1）を試す
      const regexSlash = /(\d{4})\/(\d{1,2})\/(\d{1,2})/;
      const matchesSlash = dateText.match(regexSlash);
      
      if (matchesSlash && matchesSlash.length === 4) {
        const year = parseInt(matchesSlash[1]);
        const month = parseInt(matchesSlash[2]) - 1; // 月は0-11なので1を引く
        const day = parseInt(matchesSlash[3]);
        
        return new Date(year, month, day);
      }

      // マッチしない場合は現在の日付を返す
      logger.warn(`Failed to parse Japanese date: ${dateText}, using current date instead`);
      return new Date();
    } catch (error) {
      logger.error(`Error parsing date "${dateText}": ${error}`);
      return new Date();
    }
  }
}