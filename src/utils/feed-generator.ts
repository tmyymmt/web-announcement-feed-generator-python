import { Feed } from 'feed';
import fs from 'fs';
import path from 'path';
import { Announcement, ScraperResult } from '../types';
import { logger } from './logger';

export async function generateRssFeed(
  result: ScraperResult,
  outputPath?: string,
  withDate = false
): Promise<string> {
  // フィードの基本情報を設定
  const feed = new Feed({
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

  // ファイルに書き込み
  fs.writeFileSync(finalFileName, rssOutput);
  logger.info(`RSS feed generated: ${finalFileName}`);

  return finalFileName;
}

export function getDefaultOutputPath(
  sourceUrl: string,
  withDate = false,
  extension = 'xml'
): string {
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
  } catch (error) {
    const fallbackName = withDate 
      ? `announcements_${new Date().toISOString().split('T')[0].replace(/-/g, '')}`
      : 'announcements';
    
    return `${fallbackName}.${extension}`;
  }
}