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
exports.generateRssFeed = generateRssFeed;
exports.getDefaultOutputPath = getDefaultOutputPath;
const feed_1 = require("feed");
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const logger_1 = require("./logger");
function generateRssFeed(result_1, outputPath_1) {
    return __awaiter(this, arguments, void 0, function* (result, outputPath, withDate = false) {
        // フィードの基本情報を設定
        const feed = new feed_1.Feed({
            title: `${result.source} - Announcements`,
            description: `Latest announcements from ${result.source}`,
            id: result.sourceUrl,
            link: result.sourceUrl,
            language: 'ja',
            updated: new Date(),
            generator: 'Web Announcement Feed Generator',
            copyright: `All content belongs to ${result.source}`,
        });
        // アナウンスメントをフィードに追加
        result.announcements.forEach((announcement) => {
            feed.addItem({
                title: announcement.title || 'お知らせ',
                id: announcement.link || `${result.sourceUrl}#${Date.now()}-${Math.random().toString(36).substring(2, 15)}`,
                link: announcement.link || result.sourceUrl,
                description: announcement.content,
                date: announcement.date,
                category: announcement.category ? [{ name: announcement.category }] : undefined,
            });
        });
        // RSS 2.0形式で出力
        const rssOutput = feed.rss2();
        // ファイル名の決定
        const fileName = outputPath || getDefaultOutputPath(result.sourceUrl, withDate, 'xml');
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
        // ファイルに書き込み
        fs_1.default.writeFileSync(finalFileName, rssOutput);
        logger_1.logger.info(`RSS feed generated: ${finalFileName}`);
        return finalFileName;
    });
}
function getDefaultOutputPath(sourceUrl, withDate = false, extension = 'xml') {
    try {
        const url = new URL(sourceUrl);
        const domain = url.hostname.replace(/[^a-zA-Z0-9]/g, '-');
        const pathname = url.pathname.replace(/[^a-zA-Z0-9]/g, '-').replace(/-+/g, '-');
        let fileName = `${domain}${pathname}`;
        if (fileName.endsWith('-')) {
            fileName = fileName.slice(0, -1);
        }
        if (withDate) {
            const now = new Date();
            const dateStr = `_${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`;
            fileName += dateStr;
        }
        return `${fileName}.${extension}`;
    }
    catch (error) {
        const fallbackName = withDate
            ? `announcements_${new Date().toISOString().split('T')[0].replace(/-/g, '')}`
            : 'announcements';
        return `${fallbackName}.${extension}`;
    }
}
