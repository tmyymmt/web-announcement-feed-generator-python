"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.logger = void 0;
exports.setSilentMode = setSilentMode;
const winston_1 = __importDefault(require("winston"));
// ロガーの初期設定
exports.logger = winston_1.default.createLogger({
    level: 'info',
    format: winston_1.default.format.combine(winston_1.default.format.timestamp({
        format: 'YYYY-MM-DD HH:mm:ss'
    }), winston_1.default.format.printf(info => `${info.timestamp} ${info.level}: ${info.message}`)),
    transports: [
        new winston_1.default.transports.Console()
    ]
});
// サイレントモードの設定
function setSilentMode(silent) {
    exports.logger.silent = silent;
}
