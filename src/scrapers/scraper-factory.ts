import { BaseScraper } from './base-scraper';
import { FirebaseReleasesScraper } from './firebase-google-com-support-releases-scraper';
import { MonacaHeadlineScraper } from './ja-monaca-io-headline-scraper';
import { logger } from '../utils/logger';

export class ScraperFactory {
  private static readonly SCRAPERS = {
    'https://firebase.google.com/support/releases': FirebaseReleasesScraper,
    'https://ja.monaca.io/headline/': MonacaHeadlineScraper,
  };

  static getScraper(url: string): BaseScraper {
    const ScraperClass = this.SCRAPERS[url as keyof typeof this.SCRAPERS];
    
    if (!ScraperClass) {
      logger.error(`No scraper available for URL: ${url}`);
      throw new Error(`No scraper available for URL: ${url}`);
    }
    
    logger.info(`Creating scraper for ${url}`);
    return new ScraperClass();
  }

  static getAvailableUrls(): string[] {
    return Object.keys(this.SCRAPERS);
  }
}