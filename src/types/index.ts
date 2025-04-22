export interface Announcement {
  date: Date;
  title?: string;
  content: string;
  category?: string;
  link?: string;
}

export interface ScraperResult {
  announcements: Announcement[];
  source: string;
  sourceUrl: string;
}

export interface FilterOptions {
  startDate?: Date;
  endDate?: Date;
  includeCategory?: string;
  excludeCategory?: string;
}