import { Builder, WebDriver } from 'selenium-webdriver';
import { Options } from 'selenium-webdriver/chrome';
import * as fs from 'fs';
import * as path from 'path';
import { Announcement, ScraperResult } from '../types';
import { logger } from '../utils/logger';

export abstract class BaseScraper {
  protected readonly url: string;
  protected driver: WebDriver | null = null;
  
  constructor(url: string) {
    this.url = url;
  }

  async initialize(): Promise<void> {
    try {
      // Chromeオプションの設定
      const options = new Options();
      options.addArguments('--headless');
      options.addArguments('--no-sandbox');
      options.addArguments('--disable-dev-shm-usage');
      options.addArguments('--disable-gpu');
      options.addArguments('--window-size=1920,1080');
      options.addArguments('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36');

      // ChromeDriver直接指定のオプション
      try {
        // webdriver-managerがダウンロードしたchromedriver pathを探す試み
        const modulePath = path.join(process.cwd(), 'node_modules', 'webdriver-manager', 'selenium');
        if (fs.existsSync(modulePath)) {
          const files = fs.readdirSync(modulePath);
          const chromeDriverFile = files.find(file => file.startsWith('chromedriver_') && !file.endsWith('.zip'));
          
          if (chromeDriverFile) {
            const chromedriverPath = path.join(modulePath, chromeDriverFile);
            logger.info(`Using ChromeDriver from: ${chromedriverPath}`);
            
            // ChromeDriverのパスを設定
            process.env.PATH = `${modulePath}:${process.env.PATH}`;
          }
        }
      } catch (error) {
        logger.warn(`Failed to find ChromeDriver in webdriver-manager: ${error}`);
      }

      // ドライバーの初期化
      this.driver = await new Builder()
        .forBrowser('chrome')
        .setChromeOptions(options)
        .build();
        
      logger.info(`Browser initialized for ${this.url}`);
    } catch (error) {
      logger.error(`Failed to initialize browser: ${error}`);
      throw error;
    }
  }

  async close(): Promise<void> {
    if (this.driver) {
      await this.driver.quit();
      this.driver = null;
      logger.info('Browser closed');
    }
  }

  abstract scrape(): Promise<ScraperResult>;

  protected getSourceName(): string {
    try {
      const url = new URL(this.url);
      return url.hostname;
    } catch (error) {
      return 'unknown-source';
    }
  }

  protected generateFileName(withDate = false): string {
    try {
      const url = new URL(this.url);
      const domain = url.hostname.replace(/[^a-zA-Z0-9]/g, '-');
      const path = url.pathname.replace(/[^a-zA-Z0-9]/g, '-').replace(/-+/g, '-');
      
      let fileName = `${domain}${path}`;
      if (fileName.endsWith('-')) {
        fileName = fileName.slice(0, -1);
      }
      
      if (withDate) {
        const now = new Date();
        const dateStr = `_${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`;
        fileName += dateStr;
      }
      
      return fileName;
    } catch (error) {
      const fallbackName = withDate 
        ? `announcements_${new Date().toISOString().split('T')[0].replace(/-/g, '')}`
        : 'announcements';
      
      return fallbackName;
    }
  }
}