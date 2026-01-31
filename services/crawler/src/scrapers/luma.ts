import { Page } from 'playwright';
import { ScraperStrategy, CrawlerEvent } from './base.js';
import { Log } from 'crawlee';
import fs from 'fs';

export class LumaSearchScraper implements ScraperStrategy {
    name = 'LUMA_SEARCH_V2';
    private log = new Log({ prefix: 'LumaScraper' });

    canHandle(url: string): boolean {
        return url.includes('lu.ma') && url.includes('search');
    }

    async scrape(page: Page, url: string): Promise<CrawlerEvent[]> {
        this.log.info(`Processing ${url} with Network Interception...`);
        
        const interceptedEvents: any[] = [];

        // 1. Setup Network Listener
        page.on('response', async (response) => {
            const respUrl = response.url();
            const type = response.request().resourceType();
            
            if (['image', 'stylesheet', 'font', 'media'].includes(type)) return;

            // Log everything else
            this.log.info(`🕸️ [${type}] ${respUrl.slice(-80)}`);

            const contentType = response.headers()['content-type'] || '';
            if (contentType.includes('application/json') || respUrl.includes('json')) {
                try {
                    const json = await response.json();
                     this.log.info(`  >> JSON Keys: ${Object.keys(json).slice(0, 5)}`);
                    
                     // Special Handling for Discovery Bootstrap
                     if (respUrl.includes('bootstrap-page')) {
                        if (json.places) {
                            const cm = json.places.find((p: any) => p.name.includes('Chiang Mai') || p.slug.includes('chiang-mai'));
                            this.log.info(`🇹🇭 Found Chiang Mai in Bootstrap? ${JSON.stringify(cm)}`);
                        }
                     }

                    this.recursiveFindEvents(json, interceptedEvents, respUrl);
                } catch (e) { /* ignore */ }
            }
        });

        // 2. Parse Query & Formulate External Search
        const urlObj = new URL(url);
        const userQuery = urlObj.searchParams.get('q') || 'Chiang Mai';
        const googleQuery = `site:lu.ma "${userQuery}"`;
        
        this.log.info(`🔍 Googling for: ${googleQuery}`);

        // 3. Navigate to Search Engine
        await page.goto('https://www.google.com/search?q=' + encodeURIComponent(googleQuery), { waitUntil: 'domcontentloaded' });
        
        try {
            // Wait for results
            await page.waitForSelector('div.g', { timeout: 10000 });
        } catch (e) {
            this.log.warning('Google generic selector failed, dumping HTML for debugging');
            const html = await page.content();
            fs.writeFileSync('debug_google_fail.html', html);
        }

        // 4. Extract Event URLs
        const eventLinks = await page.evaluate(() => {
            const anchors = Array.from(document.querySelectorAll('div.g a'));
            return anchors
                .map(a => a.getAttribute('href'))
                .filter(href => href && href.includes('lu.ma/') && !href.includes('google.com'))
                .slice(0, 10); // Limit to top 10
        });

        const uniqueLinks = [...new Set(eventLinks)];
        this.log.info(`Found ${uniqueLinks.length} potential event links: ${uniqueLinks.join(', ')}`);

        if (uniqueLinks.length === 0) {
            this.log.warning('⚠️ Found 0 links! Dumping HTML for debugging...');
            const html = await page.content();
            fs.writeFileSync('debug_google_empty.html', html);
        }

        // 5. Scrape Individual Event Pages
        for (const link of uniqueLinks) {
            if (!link) continue;
            try {
                this.log.info(`\n🕵️ Visiting Event: ${link}`);
                await page.goto(link, { waitUntil: 'domcontentloaded' });
                
                // Extract Data via __NEXT_DATA__
                const nextData = await page.evaluate(() => {
                    const script = document.getElementById('__NEXT_DATA__');
                    return script ? JSON.parse(script.innerText) : null;
                });

                if (nextData) {
                    this.recursiveFindEvents(nextData, interceptedEvents, link);
                } else {
                    this.log.warning('No __NEXT_DATA__ found on event page.');
                }
                
                await page.waitForTimeout(2000); 
            } catch (e) {
                this.log.error(`Failed to scrape ${link}`, e);
            }
        }

        // 6. Parse & Deduplicate
        return this.parseEvents(interceptedEvents);
    }

    private recursiveFindEvents(obj: any, events: any[], source: string) {
        if (!obj || typeof obj !== 'object') return;

        // Check if this object itself looks like an event
        if (obj.api_id && (obj.event || obj.calendar || obj.start_at)) {
             events.push({ ...obj, _source: source });
        }
        
        // Check for nested "event" object
        if (obj.event && obj.event.api_id) {
             events.push({ ...obj.event, _source: source });
        }

        // Search in arrays
        if (Array.isArray(obj)) {
            obj.forEach(item => this.recursiveFindEvents(item, events, source));
            return;
        }

        // Search in object properties
        for (const key in obj) {
            if (typeof obj[key] === 'object') {
                this.recursiveFindEvents(obj[key], events, source);
            }
        }
    }

    private parseEvents(rawEvents: any[]): CrawlerEvent[] {
        const unique = new Map<string, CrawlerEvent>();

        rawEvents.forEach(e => {
            const evt = e.event || e;
            const slug = evt.url || evt.slug || evt.api_id;
            
            if (!slug || !evt.name) return;

            const url = slug.startsWith('http') ? slug : `https://lu.ma/${slug}`;
            
            // Dedupe by URL
            if (!unique.has(url)) {
                let location = evt.location || evt.geo_address_info || evt.address;
                if (typeof location === 'object') location = JSON.stringify(location);

                unique.set(url, {
                    title: evt.name || evt.title,
                    url: url,
                    start_time: evt.start_at || evt.date,
                    end_time: evt.end_at,
                    location: location,
                    source_domain: 'lu.ma',
                    raw_html: JSON.stringify(evt), // Storing JSON as raw_html for now
                    metadata: {
                        api_id: evt.api_id,
                        cover_url: evt.cover_url
                    }
                });
            }
        });

        const results = Array.from(unique.values());
        this.log.info(`✅ Extracted ${results.length} unique events.`);
        return results;
    }
}
