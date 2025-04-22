#!/usr/bin/env node

import { Command } from 'commander';
import path from 'path';
import fs from 'fs';
import { ScraperFactory } from './scrapers/scraper-factory';
import { filterAnnouncements, filterByDiffMode, generateCsv } from './utils/csv-generator';
import { generateRssFeed, getDefaultOutputPath } from './utils/feed-generator';
import { logger, setSilentMode } from './utils/logger';
import { FilterOptions, ScraperResult } from './types';

// パッケージ情報を読み込む
let packageInfo: { version: string; name: string; };

try {
  packageInfo = JSON.parse(fs.readFileSync(path.join(__dirname, '../package.json'), 'utf8'));
} catch (error) {
  packageInfo = { version: '1.0.0', name: 'Web Announcement Feed Generator' };
}

const program = new Command();

program
  .name(packageInfo.name || 'Web Announcement Feed Generator')
  .description('指定されたWebページのお知らせ情報からフィードとCSVを生成するツール')
  .version(packageInfo.version || '1.0.0');

program
  .argument('<url>', '対象WebページのURL（"all"を指定すると全てのサイトを処理）')
  .option('-o, --output <path>', '出力ファイルのパス')
  .option('--with-date', 'ファイル名に日付を付与する')
  .option('-s, --start-date <date>', '指定日以降のお知らせをフィルタ (YYYY-MM-DD)')
  .option('-e, --end-date <date>', '指定日以前のお知らせをフィルタ (YYYY-MM-DD)')
  .option('-ic, --include-category <text>', 'カテゴリが指定文字列を含むお知らせをフィルタ')
  .option('-ec, --exclude-category <text>', 'カテゴリが指定文字列を含まないお知らせをフィルタ')
  .option('-d, --diff-mode', '前回のフィード以降の差分のみを出力')
  .option('--silent', 'ログ出力を抑制')
  .action(async (url: string, options) => {
    try {
      // サイレントモード設定
      setSilentMode(Boolean(options.silent));

      // 全URLの場合の処理
      const urlsToProcess: string[] = url.toLowerCase() === 'all' 
        ? ScraperFactory.getAvailableUrls() 
        : [url];

      for (const targetUrl of urlsToProcess) {
        logger.info(`Processing URL: ${targetUrl}`);

        // スクレイパーの取得
        const scraper = ScraperFactory.getScraper(targetUrl);

        // スクレイピング実行
        const result = await scraper.scrape();

        // フィルタリングオプションの構築
        const filterOptions: FilterOptions = {};

        if (options.startDate) {
          filterOptions.startDate = new Date(options.startDate);
        }

        if (options.endDate) {
          filterOptions.endDate = new Date(options.endDate);
        }

        if (options.includeCategory) {
          filterOptions.includeCategory = options.includeCategory;
        }

        if (options.excludeCategory) {
          filterOptions.excludeCategory = options.excludeCategory;
        }

        // 出力ファイル名の基本部分
        const outputBasePath = options.output 
          ? options.output 
          : getDefaultOutputPath(targetUrl, options.withDate, '').replace(/\.[^/.]+$/, '');

        // RSS フィードの出力
        let outputRssPath = `${outputBasePath}.xml`;
        let announcements = result.announcements;
        
        // 差分モードの場合
        if (options.diffMode && fs.existsSync(outputRssPath)) {
          announcements = await filterByDiffMode(announcements, outputRssPath);
          if (announcements.length === 0) {
            logger.info('No new announcements found since last run');
            continue;
          }
        }

        // RSS フィードの生成
        const rssFilePath = await generateRssFeed(
          { ...result, announcements },
          outputRssPath,
          options.withDate
        );

        // フィルタリングの適用
        const filteredAnnouncements = filterAnnouncements(announcements, filterOptions);
        logger.info(`Filtered ${filteredAnnouncements.length} of ${announcements.length} announcements`);

        // CSV の生成
        if (filteredAnnouncements.length > 0) {
          const csvFilePath = await generateCsv(
            filteredAnnouncements,
            targetUrl,
            `${outputBasePath}.csv`,
            options.withDate
          );
          
          logger.info(`Process completed for ${targetUrl}`);
          logger.info(`RSS file: ${rssFilePath}`);
          logger.info(`CSV file: ${csvFilePath}`);
        } else {
          logger.info('No announcements matched the filter criteria');
        }
      }

      process.exit(0);
    } catch (error) {
      logger.error(`Error: ${error}`);
      process.exit(1);
    }
  });

program.parse(process.argv);