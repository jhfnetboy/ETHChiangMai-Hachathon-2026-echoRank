import { Page } from 'playwright';

export interface CrawlerEvent {
    title: string;
    url: string;
    start_time?: string | Date;
    end_time?: string | Date;
    location?: string;
    description?: string;
    source_domain: string;
    raw_html?: string;
    metadata?: any;
}

export interface ScraperStrategy {
    /**
     * Unique key identifying this strategy (e.g., 'LUMA_SEARCH', 'DEVFOLIO_GENERIC')
     */
    name: string;

    /**
     * Main scraping method.
     * @param page Playwright Page object (already navigated to the url or ready to be)
     * @param url The target URL to scrape
     * @returns List of found events
     */
    scrape(page: Page, url: string): Promise<CrawlerEvent[]>;
    
    /**
     * Optional: Validate if this strategy can handle the given URL
     */
    canHandle(url: string): boolean;
}
