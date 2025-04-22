import winston from 'winston';

// ロガーの初期設定
export const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp({
      format: 'YYYY-MM-DD HH:mm:ss'
    }),
    winston.format.printf(info => `${info.timestamp} ${info.level}: ${info.message}`)
  ),
  transports: [
    new winston.transports.Console()
  ]
});

// サイレントモードの設定
export function setSilentMode(silent: boolean): void {
  logger.silent = silent;
}