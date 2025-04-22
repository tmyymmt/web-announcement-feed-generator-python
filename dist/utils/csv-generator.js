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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.filterAnnouncements = filterAnnouncements;
exports.generateCsv = generateCsv;
exports.filterByDiffMode = filterByDiffMode;
const csv_writer_1 = require("csv-writer");
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const logger_1 = require("./logger");
const feed_generator_1 = require("./feed-generator");
const xml2js = __importStar(require("xml2js"));
// フィルタリング関数
function filterAnnouncements(announcements, filterOptions) {
    return announcements.filter(announcement => {
        // 日付フィルタリング
        if (filterOptions.startDate && announcement.date < filterOptions.startDate) {
            return false;
        }
        if (filterOptions.endDate && announcement.date > filterOptions.endDate) {
            return false;
        }
        // カテゴリフィルタリング
        if (filterOptions.includeCategory && announcement.category) {
            if (!announcement.category.toLowerCase().includes(filterOptions.includeCategory.toLowerCase())) {
                return false;
            }
        }
        if (filterOptions.excludeCategory && announcement.category) {
            if (announcement.category.toLowerCase().includes(filterOptions.excludeCategory.toLowerCase())) {
                return false;
            }
        }
        return true;
    });
}
// CSV出力関数
function generateCsv(announcements_1, sourceUrl_1, outputPath_1) {
    return __awaiter(this, arguments, void 0, function* (announcements, sourceUrl, outputPath, withDate = false) {
        // ファイル名の決定
        const fileName = outputPath || (0, feed_generator_1.getDefaultOutputPath)(sourceUrl, withDate, 'csv');
        // ディレクトリが存在することを確認
        const directory = path_1.default.dirname(fileName);
        if (!fs_1.default.existsSync(directory)) {
            fs_1.default.mkdirSync(directory, { recursive: true });
        }
        // 差分モードの場合、既存のファイルを考慮
        let finalFileName = fileName;
        if (fs_1.default.existsSync(fileName)) {
            let counter = 1;
            const ext = path_1.default.extname(fileName);
            const base = path_1.default.basename(fileName, ext);
            const dir = path_1.default.dirname(fileName);
            while (fs_1.default.existsSync(finalFileName)) {
                finalFileName = path_1.default.join(dir, `${base}_${counter}${ext}`);
                counter++;
            }
        }
        // CSV書き込み設定
        const csvWriter = (0, csv_writer_1.createObjectCsvWriter)({
            path: finalFileName,
            header: [
                { id: 'date', title: '日付' },
                { id: 'category', title: 'カテゴリ' },
                { id: 'title', title: 'タイトル' },
                { id: 'content', title: '内容' },
                { id: 'link', title: 'リンク' }
            ],
            encoding: 'utf8'
        });
        // 日付形式を調整したデータの作成
        const records = announcements.map(announcement => ({
            date: formatDate(announcement.date),
            category: announcement.category || '',
            title: announcement.title || '',
            content: announcement.content,
            link: announcement.link || ''
        }));
        // CSVファイルへの書き込み
        yield csvWriter.writeRecords(records);
        logger_1.logger.info(`CSV file generated: ${finalFileName}`);
        return finalFileName;
    });
}
// 日付を「YYYY/MM/DD」形式にフォーマット
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}/${month}/${day}`;
}
// RSSファイルから最新の日付を取得し、その日付以降のアナウンスメントのみをフィルタリング
function filterByDiffMode(announcements, rssFilePath) {
    return __awaiter(this, void 0, void 0, function* () {
        if (!fs_1.default.existsSync(rssFilePath)) {
            logger_1.logger.info(`RSS file not found for diff mode: ${rssFilePath}`);
            return announcements;
        }
        try {
            // RSSファイルを読み込む
            const rssContent = fs_1.default.readFileSync(rssFilePath, 'utf8');
            const parser = new xml2js.Parser();
            const result = yield parser.parseStringPromise(rssContent);
            // 最新の日付を取得
            let latestDate = null;
            if (result.rss && result.rss.channel && result.rss.channel[0].item) {
                for (const item of result.rss.channel[0].item) {
                    if (item.pubDate && item.pubDate[0]) {
                        const itemDate = new Date(item.pubDate[0]);
                        if (!latestDate || itemDate > latestDate) {
                            latestDate = itemDate;
                        }
                    }
                }
            }
            if (latestDate) {
                logger_1.logger.info(`Filtering announcements after ${latestDate.toISOString()}`);
                return announcements.filter(announcement => announcement.date > latestDate);
            }
            else {
                logger_1.logger.info('No date found in RSS file for diff mode');
                return announcements;
            }
        }
        catch (error) {
            logger_1.logger.error(`Error reading RSS file for diff mode: ${error}`);
            return announcements;
        }
    });
}
