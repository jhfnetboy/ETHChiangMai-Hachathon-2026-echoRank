import { ScraperStrategy } from './base';
import { LumaSearchScraper } from './luma';

export class ScraperFactory {
    static getScraper(key: string): ScraperStrategy {
        switch (key) {
            case 'LUMA_SEARCH_V2':
                return new LumaSearchScraper();
            // Add more cases here (e.g. 'DEVFOLIO_GENERIC')
            default:
                throw new Error(`Unknown Scraper Strategy: ${key}`);
        }
    }
}
