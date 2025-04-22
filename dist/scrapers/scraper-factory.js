"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ScraperFactory = void 0;
const firebase_google_com_support_releases_scraper_1 = require("./firebase-google-com-support-releases-scraper");
const ja_monaca_io_headline_scraper_1 = require("./ja-monaca-io-headline-scraper");
const logger_1 = require("../utils/logger");
class ScraperFactory {
    static getScraper(url) {
        const ScraperClass = this.SCRAPERS[url];
        if (!ScraperClass) {
            logger_1.logger.error(`No scraper available for URL: ${url}`);
            throw new Error(`No scraper available for URL: ${url}`);
        }
        logger_1.logger.info(`Creating scraper for ${url}`);
        return new ScraperClass();
    }
    static getAvailableUrls() {
        return Object.keys(this.SCRAPERS);
    }
}
exports.ScraperFactory = ScraperFactory;
ScraperFactory.SCRAPERS = {
    'https://firebase.google.com/support/releases': firebase_google_com_support_releases_scraper_1.FirebaseReleasesScraper,
    'https://ja.monaca.io/headline/': ja_monaca_io_headline_scraper_1.MonacaHeadlineScraper,
};
