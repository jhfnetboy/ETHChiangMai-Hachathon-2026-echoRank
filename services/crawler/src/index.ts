import { PlaywrightCrawler } from 'crawlee';
import { chromium } from 'playwright';
import { Log } from 'crawlee';
import pool, { initDB } from './db';
import { ScraperFactory } from './scrapers/factory';
import { CrawlerEvent } from './scrapers/base';
import dotenv from 'dotenv';

dotenv.config();

const log = new Log({ prefix: 'Scheduler' });

// Configuration
const DEFAULT_SEED_URL = 'https://lu.ma/search?q=chiang+mai';
const DEFAULT_STRATEGY = 'LUMA_SEARCH_V2'; // Strict serial for now to avoid bans
const POLL_INTERVAL_MS = 10000; // Check DB every 10s
const MAX_CONCURRENCY = 2; // Limit parallel pages

async function seedDataSources() {
    const client = await pool.connect();
    try {
        const res = await client.query('SELECT COUNT(*) FROM data_sources');
        if (parseInt(res.rows[0].count) === 0) {
            log.info('🌱 Seeding default data sources...');
            await client.query(
                `INSERT INTO data_sources (url, frequency_hours, strategy_key) VALUES ($1, $2, $3)`,
                [DEFAULT_SEED_URL, 4, DEFAULT_STRATEGY]
            );
        }
    } finally {
        client.release();
    }
}

async function getDueSources() {
    // Select sources where last_crawled_at is null OR it's been longer than frequency_hours
    const query = `
        SELECT * FROM data_sources 
        WHERE is_active = TRUE 
        AND (
            last_crawled_at IS NULL 
            OR last_crawled_at < NOW() - (frequency_hours || ' hours')::INTERVAL
        )
        ORDER BY last_crawled_at ASC NULLS FIRST
        LIMIT 1
    `;
    const res = await pool.query(query);
    if (res.rows.length === 0) {
        // console.log('DEBUG: No due sources found.'); 
    } else {
        console.log(`DEBUG: Found ${res.rows.length} due sources. URL: ${res.rows[0].url}, Key: ${res.rows[0].strategy_key}`);
    }
    return res.rows;
}

async function saveEvents(events: CrawlerEvent[]) {
    if (events.length === 0) return;
    
    const client = await pool.connect();
    try {
        for (const event of events) {
            await client.query(
                `INSERT INTO activities (title, start_time, end_time, location, url, source_domain, raw_html, metadata)
                 VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                 ON CONFLICT (url) DO UPDATE SET 
                 title = EXCLUDED.title, 
                 start_time = EXCLUDED.start_time,
                 location = EXCLUDED.location,
                 metadata = EXCLUDED.metadata,
                 last_updated = CURRENT_TIMESTAMP`,
                [
                    event.title, 
                    event.start_time, 
                    event.end_time, 
                    event.location, 
                    event.url, 
                    event.source_domain, 
                    event.raw_html, 
                    JSON.stringify(event.metadata)
                ]
            );
        }
        log.info(`💾 Saved/Updated ${events.length} events to DB.`);
    } catch (err) {
        log.error('DB Save Error', err);
    } finally {
        client.release();
    }
}

async function updateSourceStatus(id: number) {
    await pool.query(`UPDATE data_sources SET last_crawled_at = NOW() WHERE id = $1`, [id]);
}

async function runScheduler() {
    await initDB();
    await seedDataSources();

    log.info('🚀 Crawler Scheduler Started. Polling for tasks...');

    while (true) {
        try {
            const sources = await getDueSources();
            
            if (sources.length === 0) {
                log.info('💤 No tasks due. Sleeping...');
                await new Promise(r => setTimeout(r, POLL_INTERVAL_MS));
                continue;
            }

            const source = sources[0];
            log.info(`▶️ Starting crawl for [${source.strategy_key}] ${source.url}`);

            // Instantiate Factory
            const scraper = ScraperFactory.getScraper(source.strategy_key);

            // Using Playwright directly or Crawlee? 
            // The ScraperStrategy expects a Page. We can use PlaywrightCrawler to manage the browser.
            const crawler = new PlaywrightCrawler({
                requestHandler: async ({ page, request }) => {
                    log.info(`Processing ${request.url}`);
                    const events = await scraper.scrape(page, request.url);
                    log.info(`✅ extracted ${events.length} events from ${request.url}`);
                    await saveEvents(events);
                },
                maxConcurrency: MAX_CONCURRENCY,
                headless: true,
                useSessionPool: false,
                proxyConfiguration: undefined,
                launchContext: {
                    useChrome: true,
                    launchOptions: {
                        args: [
                            '--disable-blink-features=AutomationControlled', 
                            '--no-sandbox', 
                            '--disable-setuid-sandbox',
                            '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                        ],
                        ignoreDefaultArgs: ['--enable-automation'],
                    }
                },
                preNavigationHooks: [
                    async ({ page }) => {
                        await page.addInitScript(() => {
                            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                        });
                    }
                ]
            });

            await crawler.run([source.url]);
            
            await updateSourceStatus(source.id);
            log.info(`✅ Task finished for ${source.url}`);

        } catch (error) {
            log.error('Scheduler Loop Error:', error);
            // Sleep to prevent tight error loop
            await new Promise(r => setTimeout(r, POLL_INTERVAL_MS));
        }
    }
}

// Start
runScheduler().catch(console.error);
