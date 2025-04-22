import { createObjectCsvWriter } from 'csv-writer';
import fs from 'fs';
import path from 'path';
import { Announcement, FilterOptions, ScraperResult } from '../types';
import { logger } from './logger';
import { getDefaultOutputPath } from './feed-generator';
import * as xml2js from 'xml2js';

// フィルタリング関数
export function filterAnnouncements(
  announcements: Announcement[],
  filterOptions: FilterOptions
): Announcement[] {
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
export async function generateCsv(
  announcements: Announcement[],
  sourceUrl: string,
  outputPath?: string,
  withDate = false
): Promise<string> {
  // ファイル名の決定
  const fileName = outputPath || getDefaultOutputPath(sourceUrl, withDate, 'csv');
  
  // ディレクトリが存在することを確認
  const directory = path.dirname(fileName);
  if (!fs.existsSync(directory)) {
    fs.mkdirSync(directory, { recursive: true });
  }
  
  // 差分モードの場合、既存のファイルを考慮
  let finalFileName = fileName;
  if (fs.existsSync(fileName)) {
    let counter = 1;
    const ext = path.extname(fileName);
    const base = path.basename(fileName, ext);
    const dir = path.dirname(fileName);
    
    while (fs.existsSync(finalFileName)) {
      finalFileName = path.join(dir, `${base}_${counter}${ext}`);
      counter++;
    }
  }
  
  // CSV書き込み設定
  const csvWriter = createObjectCsvWriter({
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
  await csvWriter.writeRecords(records);
  logger.info(`CSV file generated: ${finalFileName}`);
  
  return finalFileName;
}

// 日付を「YYYY/MM/DD」形式にフォーマット
function formatDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}/${month}/${day}`;
}

// RSSファイルから最新の日付を取得し、その日付以降のアナウンスメントのみをフィルタリング
export async function filterByDiffMode(
  announcements: Announcement[],
  rssFilePath: string
): Promise<Announcement[]> {
  if (!fs.existsSync(rssFilePath)) {
    logger.info(`RSS file not found for diff mode: ${rssFilePath}`);
    return announcements;
  }
  
  try {
    // RSSファイルを読み込む
    const rssContent = fs.readFileSync(rssFilePath, 'utf8');
    const parser = new xml2js.Parser();
    const result = await parser.parseStringPromise(rssContent);
    
    // 最新の日付を取得
    let latestDate: Date | null = null;
    
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
      logger.info(`Filtering announcements after ${latestDate.toISOString()}`);
      return announcements.filter(announcement => announcement.date > latestDate!);
    } else {
      logger.info('No date found in RSS file for diff mode');
      return announcements;
    }
  } catch (error) {
    logger.error(`Error reading RSS file for diff mode: ${error}`);
    return announcements;
  }
}