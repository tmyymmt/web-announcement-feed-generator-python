"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
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
exports.FirebaseReleasesScraper = void 0;
const selenium_webdriver_1 = require("selenium-webdriver");
const base_scraper_1 = require("./base-scraper");
const logger_1 = require("../utils/logger");
const fs = __importStar(require("fs"));
class FirebaseReleasesScraper extends base_scraper_1.BaseScraper {
    constructor() {
        super('https://firebase.google.com/support/releases');
        // 要件に準拠したカテゴリリスト
        this.categoryClasses = [
            'admin', 'android', 'changed', 'cli', 'cpp',
            'deprecated', 'feature', 'fixed', 'flutter',
            'functions', 'important', 'ios', 'issue',
            'javascript', 'removed', 'rules', 'unity'
        ];
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
                logger_1.logger.info('Navigating to Firebase releases page');
                yield this.driver.get(this.url);
                // ページのロードを待機
                yield this.driver.wait(selenium_webdriver_1.until.elementLocated(selenium_webdriver_1.By.css('body')), 10000);
                // JavaScriptの遅延読み込みのコンテンツが表示されるのを待機
                // Firebaseのページは動的コンテンツが多いため、長めの待機時間を設定
                yield this.driver.sleep(5000);
                // デバッグ用: HTML構造をファイルに保存
                const html = yield this.driver.getPageSource();
                fs.writeFileSync('firebase-releases-debug.html', html);
                logger_1.logger.info('Debug HTML saved to firebase-releases-debug.html');
                // メインコンテンツを取得 (changelog クラスがお知らせの一覧)
                const mainContentSelectors = [
                    '.changelog',
                    '.devsite-article-body',
                    'main',
                    '.devsite-content'
                ];
                let mainContent = null;
                for (const selector of mainContentSelectors) {
                    try {
                        mainContent = yield this.driver.findElement(selenium_webdriver_1.By.css(selector));
                        if (mainContent) {
                            logger_1.logger.info(`Found main content with selector: ${selector}`);
                            break;
                        }
                    }
                    catch (e) {
                        // このセレクタでは見つからない場合は次へ
                    }
                }
                if (!mainContent) {
                    logger_1.logger.warn('Could not find main content element, falling back to body element');
                    mainContent = yield this.driver.findElement(selenium_webdriver_1.By.css('body'));
                }
                // デバッグ用: メインコンテンツのHTMLを取得
                const mainContentHtml = yield this.driver.executeScript('return arguments[0].outerHTML', mainContent);
                fs.writeFileSync('firebase-changelog-debug.html', mainContentHtml);
                logger_1.logger.info('Debug main content HTML saved to firebase-changelog-debug.html');
                // h2要素を検索する（日付情報を含む）
                let dateElements = yield mainContent.findElements(selenium_webdriver_1.By.css('h2'));
                // デバッグ情報を表示
                logger_1.logger.info(`Found ${dateElements.length} date elements (h2)`);
                for (let i = 0; i < Math.min(dateElements.length, 5); i++) {
                    const id = (yield dateElements[i].getAttribute('id')) || 'no-id';
                    const text = yield dateElements[i].getText();
                    logger_1.logger.info(`Date element ${i}: id=${id}, text=${text}`);
                }
                // 日付形式のテキストを持つh2要素だけをフィルタリング
                const filteredDateElements = [];
                const dateRegex = /(January|February|March|April|May|June|July|August|September|October|November|December)[\s,]+\d{1,2}(,\s*\d{4}|\s+\d{4})/i;
                for (const element of dateElements) {
                    const text = yield element.getText();
                    if (dateRegex.test(text)) {
                        filteredDateElements.push(element);
                    }
                }
                logger_1.logger.info(`Found ${filteredDateElements.length} filtered date elements with date format`);
                // アナウンスメントのリストを作成
                const announcements = [];
                // 各日付要素(h2)を処理
                for (let i = 0; i < filteredDateElements.length; i++) {
                    const dateElement = filteredDateElements[i];
                    const dateText = yield dateElement.getText();
                    const date = this.parseDate(dateText);
                    logger_1.logger.info(`Processing date: ${dateText} -> ${date.toISOString()}`);
                    // h2の後のh3要素を取得するスクリプト
                    const getCategoriesScript = `
          function getCategories(dateElement, nextDateElement) {
            const categories = [];
            let currentElement = dateElement;
            
            while (currentElement = currentElement.nextElementSibling) {
              // 次の日付要素に到達したら終了
              if (nextDateElement && currentElement === nextDateElement) {
                break;
              }
              
              // h2に到達したら終了（次のセクション）
              if (currentElement.tagName === 'H2') {
                break;
              }
              
              // h3が大カテゴリ
              if (currentElement.tagName === 'H3') {
                categories.push({
                  element: currentElement,
                  title: currentElement.textContent.trim()
                });
              }
            }
            
            return categories;
          }
          
          return getCategories(arguments[0], arguments[1]);
        `;
                    // 次のh2要素までの範囲を特定
                    let nextDateElement = null;
                    if (i < filteredDateElements.length - 1) {
                        nextDateElement = filteredDateElements[i + 1];
                    }
                    // h2とh3の間のカテゴリ要素を取得
                    const categories = yield this.driver.executeScript(getCategoriesScript, dateElement, nextDateElement);
                    logger_1.logger.info(`Found ${categories.length} categories for date ${dateText}`);
                    // 各カテゴリ(h3)を処理
                    for (const category of categories) {
                        // h3の次のul要素を取得するスクリプト
                        const getAnnouncementsListScript = `
            function getAnnouncementsList(categoryElement) {
              let currentElement = categoryElement.element;
              
              // h3の次の要素を探す
              while (currentElement = currentElement.nextElementSibling) {
                // ulが見つかればそれを返す
                if (currentElement.tagName === 'UL') {
                  return currentElement;
                }
                
                // 次のh3またはh2に達したらもう無い
                if (currentElement.tagName === 'H3' || currentElement.tagName === 'H2') {
                  break;
                }
              }
              
              return null;
            }
            
            return getAnnouncementsList(arguments[0]);
          `;
                        // h3の次のul要素を取得
                        const announcementsList = yield this.driver.executeScript(getAnnouncementsListScript, category);
                        if (announcementsList) {
                            // ulの直下のli要素を取得するスクリプト
                            const getAnnouncementsScript = `
              function getAnnouncements(listElement) {
                const items = [];
                const listItems = listElement.querySelectorAll('li');
                
                for (const li of listItems) {
                  const spans = li.querySelectorAll('span');
                  let itemCategory = '';
                  let content = li.textContent.trim();
                  
                  // spanがある場合はカテゴリを取得
                  if (spans.length > 0) {
                    for (const span of spans) {
                      const classList = span.classList;
                      
                      // release-* クラスを探す
                      for (const className of classList) {
                        if (className.startsWith('release-')) {
                          itemCategory = className.replace('release-', '');
                          break;
                        }
                      }
                      
                      // カテゴリが見つかった場合はその部分を内容から除外
                      if (itemCategory) {
                        content = content.replace(span.textContent.trim(), '').trim();
                      }
                    }
                  }
                  
                  items.push({
                    category: itemCategory,
                    content: content
                  });
                }
                
                return items;
              }
              
              return getAnnouncements(arguments[0]);
            `;
                            // リスト内の各お知らせ項目を取得
                            const announcementItems = yield this.driver.executeScript(getAnnouncementsScript, announcementsList);
                            logger_1.logger.info(`Found ${announcementItems.length} announcements for category ${category.title}`);
                            // 各お知らせをアナウンスメントとして追加
                            for (const item of announcementItems) {
                                let itemCategory = item.category;
                                // カテゴリが見つからなかった場合、テキストから判定
                                if (!itemCategory) {
                                    itemCategory = this.detectCategoryFromText(item.content);
                                }
                                // カテゴリがまだ見つからなかった場合、h3のカテゴリタイトルを使用
                                if (!itemCategory && category.title) {
                                    // h3のタイトルからカテゴリを推測
                                    itemCategory = this.detectCategoryFromText(category.title);
                                }
                                announcements.push({
                                    date,
                                    content: `${category.title}: ${item.content}`,
                                    category: itemCategory,
                                    title: '', // prompt.mdによると、お知らせのタイトルは無い
                                });
                                logger_1.logger.debug(`Added announcement: ${category.title}: ${item.content.substring(0, 50)}...`);
                            }
                        }
                    }
                }
                // アナウンスメントがまだ見つからなかった場合のフォールバック処理
                if (announcements.length === 0) {
                    logger_1.logger.info('No announcements found with primary method, trying fallback approach');
                    return yield this.fallbackScrape();
                }
                logger_1.logger.info(`Total announcements found: ${announcements.length}`);
                return {
                    announcements,
                    source: 'Firebase Releases',
                    sourceUrl: this.url,
                };
            }
            catch (error) {
                logger_1.logger.error(`Error scraping Firebase releases: ${error}`);
                throw error;
            }
            finally {
                yield this.close();
            }
        });
    }
    // フォールバックとして全体の内容をスクレイピング
    fallbackScrape() {
        return __awaiter(this, void 0, void 0, function* () {
            logger_1.logger.info('Using fallback scraping method');
            // リストアイテム(li)を直接取得
            const listItems = yield this.driver.findElements(selenium_webdriver_1.By.css('li'));
            logger_1.logger.info(`Found ${listItems.length} list items`);
            // リストアイテムが少なくとも10件あれば、それらを処理
            if (listItems.length >= 10) {
                const announcements = [];
                // HTML全体を取得して解析
                const fullHtml = yield this.driver.getPageSource();
                // 日付やタイトルのパターンを使って解析
                const datePattern = /(January|February|March|April|May|June|July|August|September|October|November|December)[\s,]+\d{1,2}(,\s*\d{4}|\s+\d{4})/gi;
                const dateMatches = fullHtml.match(datePattern);
                // 最新の日付を取得
                const latestDate = dateMatches && dateMatches.length > 0
                    ? this.parseDate(dateMatches[0])
                    : new Date();
                // 各リストアイテムを処理
                for (let i = 0; i < Math.min(listItems.length, 200); i++) { // 最大200項目を処理
                    const item = listItems[i];
                    const text = yield item.getText();
                    if (text && text.length > 5) { // 短すぎる内容は無視
                        // カテゴリをクラス名から検出
                        let category = '';
                        try {
                            // リストアイテムのクラス名を取得
                            const classes = yield item.getAttribute('class');
                            if (classes) {
                                const classList = classes.split(' ');
                                // release-* クラスを探す
                                for (const className of classList) {
                                    if (className.startsWith('release-')) {
                                        category = className.replace('release-', '');
                                        break;
                                    }
                                }
                            }
                            // カテゴリが見つからない場合、子要素を確認
                            if (!category) {
                                const spans = yield item.findElements(selenium_webdriver_1.By.css('span'));
                                for (const span of spans) {
                                    const spanClasses = yield span.getAttribute('class');
                                    if (spanClasses) {
                                        const spanClassList = spanClasses.split(' ');
                                        for (const className of spanClassList) {
                                            if (className.startsWith('release-')) {
                                                category = className.replace('release-', '');
                                                break;
                                            }
                                        }
                                    }
                                    if (category)
                                        break;
                                }
                            }
                        }
                        catch (e) {
                            // クラス名の取得に失敗した場合
                        }
                        // カテゴリが見つからない場合はテキストから検出
                        if (!category) {
                            category = this.detectCategoryFromText(text);
                        }
                        // 親要素を辿って日付を探す
                        let currentDate = latestDate;
                        try {
                            // このリストアイテムの先祖要素（日付を含む可能性がある）を取得
                            const parentScript = `
              function findParentWithDate(element, levels = 5) {
                let current = element;
                let dateText = null;
                
                for (let i = 0; i < levels && current; i++) {
                  // 前の兄弟要素を確認
                  let sibling = current.previousElementSibling;
                  while (sibling) {
                    if (['H2', 'H3'].includes(sibling.tagName) && 
                        /January|February|March|April|May|June|July|August|September|October|November|December/i.test(sibling.textContent)) {
                      return sibling.textContent;
                    }
                    sibling = sibling.previousElementSibling;
                  }
                  
                  // 親要素に移動
                  current = current.parentElement;
                }
                
                return null;
              }
              
              return findParentWithDate(arguments[0]);
            `;
                            const dateText = yield this.driver.executeScript(parentScript, item);
                            if (dateText) {
                                currentDate = this.parseDate(dateText);
                            }
                        }
                        catch (e) {
                            // 親要素の取得に失敗した場合、最新の日付を使用
                        }
                        announcements.push({
                            date: currentDate,
                            content: text,
                            category,
                            title: '', // prompt.mdによると、お知らせのタイトルは無い
                        });
                    }
                }
                if (announcements.length > 0) {
                    return {
                        announcements,
                        source: 'Firebase Releases',
                        sourceUrl: this.url,
                    };
                }
            }
            // それでも要素が見つからない場合は、全文をスクレイプしてパースする
            logger_1.logger.info('No release notes found with CSS selectors. Trying to parse the whole content');
            const body = yield this.driver.findElement(selenium_webdriver_1.By.css('body'));
            const content = yield body.getText();
            const announcements = this.parseContentText(content);
            return {
                announcements,
                source: 'Firebase Releases',
                sourceUrl: this.url,
            };
        });
    }
    // テキストコンテンツからリリース情報をパースする
    parseContentText(content) {
        const announcements = [];
        // 日付のパターン (例: "January 15, 2023" や "2023-01-15")
        const datePatterns = [
            /(\w+ \d{1,2}, \d{4})/g, // January 15, 2023
            /(\d{4}-\d{2}-\d{2})/g, // 2023-01-15
            /(\d{2}\/\d{2}\/\d{4})/g, // 01/15/2023
        ];
        // 日付で文章を分割する
        let lastIndex = 0;
        let lastDate = null;
        // 複数のパターンで試みる
        for (const pattern of datePatterns) {
            const matches = content.matchAll(pattern);
            const matchArray = Array.from(matches);
            for (let i = 0; i < matchArray.length; i++) {
                const match = matchArray[i];
                if (match.index !== undefined && match.index > lastIndex) {
                    const dateText = match[0];
                    const date = new Date(dateText);
                    // 日付が有効であれば項目として追加
                    if (!isNaN(date.getTime())) {
                        lastDate = date;
                        lastIndex = match.index;
                        // 日付の後の内容を取得（次の日付まで、または最大2000文字）
                        const nextMatch = matchArray[i + 1];
                        const endIndex = nextMatch
                            ? nextMatch.index
                            : Math.min(content.length, match.index + dateText.length + 2000);
                        const itemContent = content.substring(match.index + dateText.length, endIndex).trim();
                        // 空でないコンテンツの場合のみ追加
                        if (itemContent) {
                            // カテゴリ判定
                            let category = this.detectCategoryFromText(itemContent);
                            // コンテンツを複数の段落に分割
                            const paragraphs = itemContent.split(/\n\s*\n/);
                            // 各段落をアナウンスメントとして追加
                            for (const paragraph of paragraphs) {
                                if (paragraph.trim().length > 20) { // 短すぎるものは無視
                                    announcements.push({
                                        date: date,
                                        content: paragraph.trim(),
                                        category,
                                        title: '', // prompt.mdによると、お知らせのタイトルは無い
                                    });
                                }
                            }
                        }
                    }
                }
            }
            // いくつか見つかった場合は、このパターンで十分
            if (announcements.length > 5) {
                break;
            }
        }
        // テキストから日付情報を抽出できなかった場合のフォールバック
        if (announcements.length === 0) {
            // 空行で区切られた段落を各アナウンスメントとして扱う
            const paragraphs = content.split(/\n\s*\n/);
            for (let i = 0; i < paragraphs.length; i++) {
                const paragraph = paragraphs[i].trim();
                if (paragraph.length > 20) { // 短すぎるものは無視
                    announcements.push({
                        date: new Date(), // 日付不明の場合は現在日時
                        content: paragraph,
                        title: '', // prompt.mdによると、お知らせのタイトルは無い
                        category: this.detectCategoryFromText(paragraph),
                    });
                }
            }
        }
        return announcements;
    }
    // テキストからカテゴリを検出
    detectCategoryFromText(text) {
        const lowerText = text.toLowerCase();
        // prompt.mdに記載されたキーワードに基づくカテゴリ検出
        if (lowerText.includes('deprecated') || lowerText.includes('提供終了') || lowerText.includes('廃止')) {
            return 'deprecated';
        }
        else if (lowerText.includes('shutdown') || lowerText.includes('shutodown')) { // typoも含めて対応
            return 'removed'; // shutdownはremovedカテゴリとして扱う
        }
        else if (lowerText.includes('important') || lowerText.includes('重要')) {
            return 'important';
        }
        else if (lowerText.includes('feature')) {
            return 'feature';
        }
        else if (lowerText.includes('fixed') || lowerText.includes('fix')) {
            return 'fixed';
        }
        else if (lowerText.includes('admin')) {
            return 'admin';
        }
        else if (lowerText.includes('android')) {
            return 'android';
        }
        else if (lowerText.includes('ios')) {
            return 'ios';
        }
        // 他のカテゴリもチェック
        for (const category of this.categoryClasses) {
            if (lowerText.includes(category)) {
                return category;
            }
        }
        return '';
    }
    parseDate(dateText) {
        try {
            // 様々な日付形式をサポート
            const date = new Date(dateText);
            if (!isNaN(date.getTime())) {
                return date;
            }
            // 既知の形式でパース
            // 例: "January 15, 2023"
            const monthNames = [
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ];
            const regexFull = new RegExp(`(${monthNames.join('|')}) (\\d{1,2})(,|\\s)\\s*(\\d{4})`, 'i');
            const matchesFull = dateText.match(regexFull);
            if (matchesFull) {
                const month = monthNames.findIndex(m => m.toLowerCase() === matchesFull[1].toLowerCase());
                if (month !== -1) {
                    const day = parseInt(matchesFull[2]);
                    const year = parseInt(matchesFull[4]);
                    return new Date(year, month, day);
                }
            }
            // 形式: "2023-01-15" または "2023/01/15"
            const regexYMD = /(\d{4})[-\/](\d{1,2})[-\/](\d{1,2})/;
            const matchesYMD = dateText.match(regexYMD);
            if (matchesYMD) {
                const year = parseInt(matchesYMD[1]);
                const month = parseInt(matchesYMD[2]) - 1; // 月は0-11
                const day = parseInt(matchesYMD[3]);
                return new Date(year, month, day);
            }
            // 形式: "01/15/2023" (米国形式)
            const regexMDY = /(\d{1,2})\/(\d{1,2})\/(\d{4})/;
            const matchesMDY = dateText.match(regexMDY);
            if (matchesMDY) {
                const month = parseInt(matchesMDY[1]) - 1; // 月は0-11
                const day = parseInt(matchesMDY[2]);
                const year = parseInt(matchesMDY[3]);
                return new Date(year, month, day);
            }
            // マッチしない場合は現在の日付を返す
            logger_1.logger.error(`Failed to parse date: ${dateText}, using current date instead`);
            return new Date();
        }
        catch (error) {
            logger_1.logger.error(`Error parsing date "${dateText}": ${error}`);
            return new Date();
        }
    }
}
exports.FirebaseReleasesScraper = FirebaseReleasesScraper;
