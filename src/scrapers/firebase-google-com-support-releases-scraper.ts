import { By, until, WebElement } from 'selenium-webdriver';
import { BaseScraper } from './base-scraper';
import { Announcement, ScraperResult } from '../types';
import { logger } from '../utils/logger';
import * as fs from 'fs';
import * as path from 'path';

export class FirebaseReleasesScraper extends BaseScraper {
  // 要件に準拠したカテゴリリスト
  private readonly categoryClasses = [
    'admin', 'android', 'changed', 'cli', 'cpp', 
    'deprecated', 'feature', 'fixed', 'flutter', 
    'functions', 'important', 'ios', 'issue', 
    'javascript', 'removed', 'rules', 'unity'
  ];

  constructor() {
    super('https://firebase.google.com/support/releases');
  }

  async scrape(): Promise<ScraperResult> {
    if (!this.driver) {
      await this.initialize();
    }

    if (!this.driver) {
      throw new Error('Failed to initialize WebDriver');
    }

    try {
      logger.info('Navigating to Firebase releases page');
      await this.driver.get(this.url);

      // ページのロードを待機
      await this.driver.wait(until.elementLocated(By.css('body')), 10000);
      
      // JavaScriptの遅延読み込みのコンテンツが表示されるのを待機
      // Firebaseのページは動的コンテンツが多いため、長めの待機時間を設定
      await this.driver.sleep(5000);

      // デバッグ用: HTML構造をファイルに保存
      const html = await this.driver.getPageSource();
      fs.writeFileSync('firebase-releases-debug.html', html);
      logger.info('Debug HTML saved to firebase-releases-debug.html');

      // メインコンテンツを取得 (.devsite-article-bodyやメインコンテナなど複数のセレクタを試行)
      const mainContentSelectors = [
        '.changelog',
        '.devsite-article-body',
        'main',
        '.devsite-content'
      ];
      
      let mainContent: WebElement | null = null;
      
      for (const selector of mainContentSelectors) {
        try {
          mainContent = await this.driver.findElement(By.css(selector));
          if (mainContent) {
            logger.info(`Found main content with selector: ${selector}`);
            break;
          }
        } catch (e) {
          // このセレクタでは見つからない場合は次へ
        }
      }
      
      if (!mainContent) {
        logger.warn('Could not find main content element, falling back to body element');
        mainContent = await this.driver.findElement(By.css('body'));
      }

      // デバッグ用: メインコンテンツのHTMLを取得
      const mainContentHtml = await this.driver.executeScript(
        'return arguments[0].outerHTML', 
        mainContent
      );
      fs.writeFileSync('firebase-changelog-debug.html', mainContentHtml as string);
      logger.info('Debug main content HTML saved to firebase-changelog-debug.html');

      // h2要素を検索する（日付情報を含む可能性が高い）
      let dateElements = await mainContent.findElements(By.css('h2'));
      
      // デバッグ情報を表示
      logger.info(`Found ${dateElements.length} date elements (h2)`);
      for (let i = 0; i < Math.min(dateElements.length, 5); i++) {
        const id = await dateElements[i].getAttribute('id') || 'no-id';
        const text = await dateElements[i].getText();
        logger.info(`Date element ${i}: id=${id}, text=${text}`);
      }
      
      // 日付形式のテキストを持つh2要素だけをフィルタリング
      const filteredDateElements: WebElement[] = [];
      const dateRegex = /(January|February|March|April|May|June|July|August|September|October|November|December)[\s,]+\d{1,2}(,\s*\d{4}|\s+\d{4})/i;
      
      for (const element of dateElements) {
        const text = await element.getText();
        if (dateRegex.test(text)) {
          filteredDateElements.push(element);
        }
      }
      
      logger.info(`Found ${filteredDateElements.length} filtered date elements with date format`);

      // アナウンスメントのリストを作成
      const announcements: Announcement[] = [];

      // 各日付要素を処理
      for (let i = 0; i < filteredDateElements.length; i++) {
        const dateElement = filteredDateElements[i];
        const dateText = await dateElement.getText();
        const date = this.parseDate(dateText);
        
        logger.info(`Processing date: ${dateText} -> ${date.toISOString()}`);
        
        // 次のh2要素までの範囲を特定
        let nextDateElement = null;
        if (i < filteredDateElements.length - 1) {
          nextDateElement = filteredDateElements[i + 1];
        }
        
        // この日付の直後の要素から次のh2までのすべての内容を取得するためのスクリプト
        const script = `
          function getReleaseContent(dateElement, nextDateElement) {
            let content = '';
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
              
              // 内容を追加
              if (currentElement.textContent && currentElement.textContent.trim()) {
                content += currentElement.outerHTML + '\\n';
              }
            }
            
            return content;
          }
          
          return getReleaseContent(arguments[0], arguments[1]);
        `;
        
        // スクリプトを実行して日付間のコンテンツを取得
        const contentHtml = await this.driver.executeScript(script, dateElement, nextDateElement) as string;
        
        // リリースコンテンツを直接ブラウザ内でJavaScriptを使用して解析
        const extractionScript = `
          function extractSections(html) {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            
            const sections = [];
            
            // h3/h4要素を探す（セクションのタイトルとして）
            const h3Elements = tempDiv.querySelectorAll('h3, h4');
            
            // h3/h4要素があれば、それをセクションとして処理
            if (h3Elements.length > 0) {
              for (let i = 0; i < h3Elements.length; i++) {
                const h3 = h3Elements[i];
                const title = h3.textContent.trim();
                const items = [];
                
                // 次のセクションまでの要素を取得
                let nextElement = h3.nextElementSibling;
                const nextH3 = (i < h3Elements.length - 1) ? h3Elements[i + 1] : null;
                
                while (nextElement && nextElement !== nextH3) {
                  // リスト要素の場合は各アイテムを抽出
                  if (nextElement.tagName === 'UL' || nextElement.tagName === 'OL') {
                    const listItems = nextElement.querySelectorAll('li');
                    for (const li of listItems) {
                      const itemText = li.textContent.trim();
                      if (itemText) {
                        items.push(itemText);
                      }
                    }
                  }
                  // 段落の場合はそのまま追加
                  else if (nextElement.tagName === 'P') {
                    const pText = nextElement.textContent.trim();
                    if (pText) {
                      items.push(pText);
                    }
                  }
                  
                  nextElement = nextElement.nextElementSibling;
                }
                
                // アイテムがあれば、セクションとして追加
                if (items.length > 0) {
                  sections.push({ title, items });
                }
              }
            }
            
            // h3要素がない場合や、h3要素の後にリストがない場合のフォールバック
            if (sections.length === 0) {
              // リスト要素を直接検索
              const lists = tempDiv.querySelectorAll('ul, ol');
              
              for (const list of lists) {
                const items = [];
                const listItems = list.querySelectorAll('li');
                
                for (const li of listItems) {
                  const itemText = li.textContent.trim();
                  if (itemText) {
                    items.push(itemText);
                  }
                }
                
                // 前の要素がタイトルとして使えるか確認
                let title = '';
                if (list.previousElementSibling) {
                  const prevElement = list.previousElementSibling;
                  if (['H3', 'H4', 'P', 'DIV'].includes(prevElement.tagName)) {
                    title = prevElement.textContent.trim();
                  }
                }
                
                if (items.length > 0) {
                  sections.push({ title, items });
                }
              }
            }
            
            return JSON.stringify(sections);
          }
          
          return extractSections(arguments[0]);
        `;
        
        // ブラウザ内でセクションを抽出
        const extractedSections = await this.driver.executeScript(extractionScript, contentHtml) as string;
        let sections: { title: string, items: string[] }[] = [];
        
        try {
          sections = JSON.parse(extractedSections);
        } catch (error) {
          logger.error(`Error parsing extracted sections: ${error}`);
        }
        
        logger.info(`Found ${sections.length} sections for date ${dateText}`);
        
        // 抽出したセクションからアナウンスメントを生成
        for (const section of sections) {
          if (section.title && section.items.length > 0) {
            // このセクション内の各項目をアナウンスメントとして追加
            for (const item of section.items) {
              let category = this.detectCategoryFromText(item);
              
              announcements.push({
                date,
                content: `${section.title}: ${item}`,
                category,
                title: '', // prompt.mdによると、お知らせのタイトルは無い
              });
              
              logger.debug(`Added announcement: ${section.title}: ${item.substring(0, 50)}...`);
            }
          } else if (section.items.length > 0) {
            // タイトルがない場合は各項目を直接アナウンスメントとして追加
            for (const item of section.items) {
              let category = this.detectCategoryFromText(item);
              
              announcements.push({
                date,
                content: item,
                category,
                title: '', // prompt.mdによると、お知らせのタイトルは無い
              });
              
              logger.debug(`Added announcement without section title: ${item.substring(0, 50)}...`);
            }
          }
        }
        
        // ブラウザ側でリスト要素を直接抽出する代替アプローチ
        if (sections.length === 0 || announcements.length === 0) {
          logger.info('No sections or announcements found, trying direct list extraction');
          
          const listExtractionScript = `
            function extractListItems(html) {
              const tempDiv = document.createElement('div');
              tempDiv.innerHTML = html;
              
              const result = [];
              
              // リスト要素を検出
              const lists = tempDiv.querySelectorAll('ul, ol');
              
              for (const list of lists) {
                const items = [];
                const listItems = list.querySelectorAll('li');
                
                for (const item of listItems) {
                  const content = item.textContent.trim();
                  if (content) {
                    items.push(content);
                  }
                }
                
                if (items.length > 0) {
                  result.push(...items);
                }
              }
              
              return result;
            }
            
            return extractListItems(arguments[0]);
          `;
          
          const listItems = await this.driver.executeScript(listExtractionScript, contentHtml) as string[];
          
          for (const item of listItems) {
            let category = this.detectCategoryFromText(item);
            
            announcements.push({
              date,
              content: item,
              category,
              title: '', // prompt.mdによると、お知らせのタイトルは無い
            });
            
            logger.debug(`Added announcement from direct list: ${item.substring(0, 50)}...`);
          }
        }
      }

      // アナウンスメントがまだ見つからなかった場合のフォールバック処理
      if (announcements.length === 0) {
        logger.info('No announcements found with primary method, trying fallback approach');
        return await this.fallbackScrape();
      }

      logger.info(`Total announcements found: ${announcements.length}`);
      return {
        announcements,
        source: 'Firebase Releases',
        sourceUrl: this.url,
      };
    } catch (error) {
      logger.error(`Error scraping Firebase releases: ${error}`);
      throw error;
    } finally {
      await this.close();
    }
  }

  // フォールバックとして全体の内容をスクレイピング
  private async fallbackScrape(): Promise<ScraperResult> {
    logger.info('Using fallback scraping method');
    
    // リストアイテムを直接取得
    const listItems = await this.driver!.findElements(By.css('li'));
    logger.info(`Found ${listItems.length} list items`);
    
    // リストアイテムが少なくとも10件あれば、それらを処理
    if (listItems.length >= 10) {
      const announcements: Announcement[] = [];
      
      // HTML全体を取得して解析
      const fullHtml = await this.driver!.getPageSource();
      
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
        const text = await item.getText();
        
        if (text && text.length > 5) { // 短すぎる内容は無視
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
            
            const dateText = await this.driver!.executeScript(parentScript, item) as string;
            
            if (dateText) {
              currentDate = this.parseDate(dateText);
            }
          } catch (e) {
            // 親要素の取得に失敗した場合、最新の日付を使用
          }
          
          let category = this.detectCategoryFromText(text);
          
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
    logger.info('No release notes found with CSS selectors. Trying to parse the whole content');
    const body = await this.driver!.findElement(By.css('body'));
    const content = await body.getText();
    
    const announcements = this.parseContentText(content);
    return {
      announcements,
      source: 'Firebase Releases',
      sourceUrl: this.url,
    };
  }

  // テキストコンテンツからリリース情報をパースする
  private parseContentText(content: string): Announcement[] {
    const announcements: Announcement[] = [];
    
    // 日付のパターン (例: "January 15, 2023" や "2023-01-15")
    const datePatterns = [
      /(\w+ \d{1,2}, \d{4})/g,  // January 15, 2023
      /(\d{4}-\d{2}-\d{2})/g,   // 2023-01-15
      /(\d{2}\/\d{2}\/\d{4})/g, // 01/15/2023
    ];
    
    // 日付で文章を分割する
    let lastIndex = 0;
    let lastDate: Date | null = null;
    
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
              
            const itemContent = content.substring(match.index + dateText.length, endIndex as number).trim();
            
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
  private detectCategoryFromText(text: string): string {
    const lowerText = text.toLowerCase();
    
    // prompt.mdに記載されたキーワードに基づくカテゴリ検出
    if (lowerText.includes('deprecated') || lowerText.includes('提供終了') || lowerText.includes('廃止')) {
      return 'deprecated';
    } else if (lowerText.includes('shutdown') || lowerText.includes('shutodown')) { // typoも含めて対応
      return 'removed'; // shutdownはremovedカテゴリとして扱う
    } else if (lowerText.includes('important') || lowerText.includes('重要')) {
      return 'important';
    } else if (lowerText.includes('feature')) {
      return 'feature';
    } else if (lowerText.includes('fixed') || lowerText.includes('fix')) {
      return 'fixed';
    } else if (lowerText.includes('admin')) {
      return 'admin';
    } else if (lowerText.includes('android')) {
      return 'android';
    } else if (lowerText.includes('ios')) {
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

  private parseDate(dateText: string): Date {
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
      logger.error(`Failed to parse date: ${dateText}, using current date instead`);
      return new Date();
    } catch (error) {
      logger.error(`Error parsing date "${dateText}": ${error}`);
      return new Date();
    }
  }
}