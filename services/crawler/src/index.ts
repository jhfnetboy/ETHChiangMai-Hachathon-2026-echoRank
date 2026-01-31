import { PlaywrightCrawler, Dataset } from 'crawlee';
import { initDB } from './db.js';
import pool from './db.js';
import dotenv from 'dotenv';
import { GoogleGenerativeAI } from '@google/generative-ai';

dotenv.config();

// Simple rule cache (in-memory for MVP, Redis for scale)
const ruleCache: Record<string, any> = {};

// Initialize Gemini
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || '');

import { generateSelectorsWithAI, ScrapingRule } from './rag-parser.js';

async function getOrGenerateRule(domain: string, htmlSnippet: string) {
    if (ruleCache[domain]) return ruleCache[domain];

    // Check DB
    const res = await pool.query('SELECT * FROM scraping_rules WHERE domain = $1', [domain]);
    if (res.rows.length > 0) {
        ruleCache[domain] = res.rows[0];
        return res.rows[0];
    }

    // Generate with AI
    console.log(`🤖 Generating rules for ${domain} with AI...`);
    const newRule = await generateSelectorsWithAI(domain, htmlSnippet);
    
    // Save to DB
    await pool.query(
        `INSERT INTO scraping_rules (domain, event_card_selector, title_selector, date_selector, location_selector, link_selector)
         VALUES ($1, $2, $3, $4, $5, $6) RETURNING *`,
        [domain, newRule.event_card_selector, newRule.title_selector, newRule.date_selector, newRule.location_selector, newRule.link_selector]
    );

    ruleCache[domain] = newRule;
    return newRule;
}

const crawler = new PlaywrightCrawler({
    headless: true, // Set to false to see the browser
    maxRequestsPerCrawl: 50,
    async requestHandler({ page, request, log }) {
        log.info(`Processing ${request.url}...`);
        
        const domain = new URL(request.url).hostname;
        
        // 1. Get Rules (Adaptive)
        // Extract a representative snippet (e.g., first 2000 chars of body) for AI analysis if needed
        const content = await page.content(); 
        const rule = await getOrGenerateRule(domain, content.substring(0, 5000));
        
        log.info(`Using rules for ${domain}:`, rule);

        // 2. Scrape Data
        const events = await page.$$eval(rule.event_card_selector, (cards: any[], r: any) => {
            return cards.map(card => {
                const title = card.querySelector(r.title_selector)?.innerText?.trim();
                const date = card.querySelector(r.date_selector)?.innerText?.trim();
                const location = card.querySelector(r.location_selector)?.innerText?.trim();
                const link = card.querySelector(r.link_selector)?.href;
                
                return { title, date, location, link };
            }).filter(e => e.title && e.link); // Basic filter
        }, rule);

        log.info(`Found ${events.length} events on ${request.url}`);

        // 3. Save to DB
        // For loop to save each event (basic upsert)
        for (const event of events) {
            try {
                // Ensure URL is absolute
                const absoluteUrl = new URL(event.link, request.url).href;
                
                await pool.query(
                    `INSERT INTO activities (title, location, url, source_domain, raw_html)
                     VALUES ($1, $2, $3, $4, $5)
                     ON CONFLICT (url) DO UPDATE SET 
                     title = EXCLUDED.title, 
                     location = EXCLUDED.location,
                     last_updated = CURRENT_TIMESTAMP`,
                    [event.title, event.location, absoluteUrl, domain, JSON.stringify(event)]
                );
            } catch (err) {
                log.error(`Failed to save event: ${event.title}`, err as any);
            }
        }
    },
});

// Entry Point
async function main() {
    await initDB();
    
    // Add start URLs
    await crawler.run([
        'https://lu.ma/chiang-mai', // Example
        // 'https://devfolio.co/hackathons', 
    ]);
    
    console.log('✅ Crawl finished.');
    process.exit(0);
}

main();
