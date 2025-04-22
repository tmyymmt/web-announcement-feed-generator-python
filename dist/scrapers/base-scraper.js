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
exports.BaseScraper = void 0;
const selenium_webdriver_1 = require("selenium-webdriver");
const chrome_1 = require("selenium-webdriver/chrome");
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const logger_1 = require("../utils/logger");
class BaseScraper {
    constructor(url) {
        this.driver = null;
        this.url = url;
    }
    initialize() {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                // Chromeオプションの設定
                const options = new chrome_1.Options();
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
                            logger_1.logger.info(`Using ChromeDriver from: ${chromedriverPath}`);
                            // ChromeDriverのパスを設定
                            process.env.PATH = `${modulePath}:${process.env.PATH}`;
                        }
                    }
                }
                catch (error) {
                    logger_1.logger.warn(`Failed to find ChromeDriver in webdriver-manager: ${error}`);
                }
                // ドライバーの初期化
                this.driver = yield new selenium_webdriver_1.Builder()
                    .forBrowser('chrome')
                    .setChromeOptions(options)
                    .build();
                logger_1.logger.info(`Browser initialized for ${this.url}`);
            }
            catch (error) {
                logger_1.logger.error(`Failed to initialize browser: ${error}`);
                throw error;
            }
        });
    }
    close() {
        return __awaiter(this, void 0, void 0, function* () {
            if (this.driver) {
                yield this.driver.quit();
                this.driver = null;
                logger_1.logger.info('Browser closed');
            }
        });
    }
    getSourceName() {
        try {
            const url = new URL(this.url);
            return url.hostname;
        }
        catch (error) {
            return 'unknown-source';
        }
    }
    generateFileName(withDate = false) {
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
        }
        catch (error) {
            const fallbackName = withDate
                ? `announcements_${new Date().toISOString().split('T')[0].replace(/-/g, '')}`
                : 'announcements';
            return fallbackName;
        }
    }
}
exports.BaseScraper = BaseScraper;
