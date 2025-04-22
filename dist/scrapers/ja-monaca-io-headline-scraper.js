"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.MonacaHeadlineScraper = void 0;
const selenium_webdriver_1 = require("selenium-webdriver");
const base_scraper_1 = require("./base-scraper");
const logger_1 = require("../utils/logger");
class MonacaHeadlineScraper extends base_scraper_1.BaseScraper {
    constructor() {
        super('https://ja.monaca.io/headline/');
    }
    scrape() {
        return __awaiter(this, void 0, void 0, function* () {
            if (!this.driver) {
                yield this.initialize();
            }
            if (!this.driver) {
                throw new Error('Failed to initialize WebDriver');
            }
            try {
                logger_1.logger.info('Navigating to Monaca headline page');
                yield this.driver.get(this.url);
                // ページのロードを待機
                yield this.driver.wait(selenium_webdriver_1.until.elementLocated(selenium_webdriver_1.By.css('body')), 10000);
                // JavaScriptの遅延読み込みのコンテンツが表示されるのを待機
                yield this.driver.sleep(3000);
                // お知らせ要素を全て取得
                const headlineEntries = yield this.driver.findElements(selenium_webdriver_1.By.css('.headline-entry'));
                logger_1.logger.info(`Found ${headlineEntries.length} headline entries`);
                // アナウンスメントのリストを作成
                const announcements = [];
                for (const entry of headlineEntries) {
                    try {
                        const announcement = yield this.parseHeadlineEntry(entry);
                        if (announcement) {
                            announcements.push(announcement);
                        }
                    }
                    catch (error) {
                        logger_1.logger.error(`Error parsing headline entry: ${error}`);
                    }
                }
                return {
                    announcements,
                    source: 'Monaca Headline',
                    sourceUrl: this.url,
                };
            }
            catch (error) {
                logger_1.logger.error(`Error scraping Monaca headline: ${error}`);
                throw error;
            }
            finally {
                yield this.close();
            }
        });
    }
    parseHeadlineEntry(element) {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                // お知らせの日付を取得
                const dateElement = yield element.findElement(selenium_webdriver_1.By.css('.headline-entry-date')).catch(() => null);
                if (!dateElement) {
                    logger_1.logger.debug('Headline entry has no date, skipping');
                    return null;
                }
                const dateText = yield dateElement.getText();
                const date = this.parseJapaneseDate(dateText);
                // お知らせの内容を取得
                const contentElement = yield element.findElement(selenium_webdriver_1.By.css('.headline-entry-content')).catch(() => null);
                if (!contentElement) {
                    logger_1.logger.debug('Headline entry has no content, skipping');
                    return null;
                }
                const content = yield contentElement.getText();
                // お知らせのカテゴリを取得
                const categoryElement = yield element.findElement(selenium_webdriver_1.By.css('.headline-entry-type-badge')).catch(() => null);
                let category = '';
                if (categoryElement) {
                    category = yield categoryElement.getText();
                }
                // カテゴリがない場合は内容から推測
                if (!category) {
                    const contentLower = content.toLowerCase();
                    if (contentLower.includes('deprecated') || contentLower.includes('提供終了') || contentLower.includes('廃止')) {
                        category = '提供終了';
                    }
                    else if (contentLower.includes('shutdown')) {
                        category = '終了';
                    }
                    else if (contentLower.includes('important') || contentLower.includes('重要')) {
                        category = '重要';
                    }
                }
                // リンクがあれば取得
                let link;
                const linkElement = yield element.findElement(selenium_webdriver_1.By.css('a')).catch(() => null);
                if (linkElement) {
                    link = yield linkElement.getAttribute('href');
                }
                return {
                    date,
                    content,
                    category,
                    link,
                };
            }
            catch (error) {
                logger_1.logger.error(`Error parsing headline entry element: ${error}`);
                return null;
            }
        });
    }
    parseJapaneseDate(dateText) {
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
            logger_1.logger.warn(`Failed to parse Japanese date: ${dateText}, using current date instead`);
            return new Date();
        }
        catch (error) {
            logger_1.logger.error(`Error parsing date "${dateText}": ${error}`);
            return new Date();
        }
    }
}
exports.MonacaHeadlineScraper = MonacaHeadlineScraper;
