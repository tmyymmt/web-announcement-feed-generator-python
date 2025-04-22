#!/usr/bin/env node
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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const commander_1 = require("commander");
const path_1 = __importDefault(require("path"));
const fs_1 = __importDefault(require("fs"));
const scraper_factory_1 = require("./scrapers/scraper-factory");
const csv_generator_1 = require("./utils/csv-generator");
const feed_generator_1 = require("./utils/feed-generator");
const logger_1 = require("./utils/logger");
// パッケージ情報を読み込む
let packageInfo;
try {
    packageInfo = JSON.parse(fs_1.default.readFileSync(path_1.default.join(__dirname, '../package.json'), 'utf8'));
}
catch (error) {
    packageInfo = { version: '1.0.0', name: 'Web Announcement Feed Generator' };
}
const program = new commander_1.Command();
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
    .action((url, options) => __awaiter(void 0, void 0, void 0, function* () {
    try {
        // サイレントモード設定
        (0, logger_1.setSilentMode)(Boolean(options.silent));
        // 全URLの場合の処理
        const urlsToProcess = url.toLowerCase() === 'all'
            ? scraper_factory_1.ScraperFactory.getAvailableUrls()
            : [url];
        for (const targetUrl of urlsToProcess) {
            logger_1.logger.info(`Processing URL: ${targetUrl}`);
            // スクレイパーの取得
            const scraper = scraper_factory_1.ScraperFactory.getScraper(targetUrl);
            // スクレイピング実行
            const result = yield scraper.scrape();
            // フィルタリングオプションの構築
            const filterOptions = {};
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
                : (0, feed_generator_1.getDefaultOutputPath)(targetUrl, options.withDate, '').replace(/\.[^/.]+$/, '');
            // RSS フィードの出力
            let outputRssPath = `${outputBasePath}.xml`;
            let announcements = result.announcements;
            // 差分モードの場合
            if (options.diffMode && fs_1.default.existsSync(outputRssPath)) {
                announcements = yield (0, csv_generator_1.filterByDiffMode)(announcements, outputRssPath);
                if (announcements.length === 0) {
                    logger_1.logger.info('No new announcements found since last run');
                    continue;
                }
            }
            // RSS フィードの生成
            const rssFilePath = yield (0, feed_generator_1.generateRssFeed)(Object.assign(Object.assign({}, result), { announcements }), outputRssPath, options.withDate);
            // フィルタリングの適用
            const filteredAnnouncements = (0, csv_generator_1.filterAnnouncements)(announcements, filterOptions);
            logger_1.logger.info(`Filtered ${filteredAnnouncements.length} of ${announcements.length} announcements`);
            // CSV の生成
            if (filteredAnnouncements.length > 0) {
                const csvFilePath = yield (0, csv_generator_1.generateCsv)(filteredAnnouncements, targetUrl, `${outputBasePath}.csv`, options.withDate);
                logger_1.logger.info(`Process completed for ${targetUrl}`);
                logger_1.logger.info(`RSS file: ${rssFilePath}`);
                logger_1.logger.info(`CSV file: ${csvFilePath}`);
            }
            else {
                logger_1.logger.info('No announcements matched the filter criteria');
            }
        }
        process.exit(0);
    }
    catch (error) {
        logger_1.logger.error(`Error: ${error}`);
        process.exit(1);
    }
}));
program.parse(process.argv);
