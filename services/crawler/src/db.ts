
import pg from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const pool = new pg.Pool({
    user: process.env.POSTGRES_USER || process.env.USER || 'postgres', // Default to current system user for brew
    password: process.env.POSTGRES_PASSWORD || '', // Brew often has no password default
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    database: process.env.POSTGRES_DB || 'echorank_crawler',
});

// Initialize Tables
export async function initDB() {
    const client = await pool.connect();
    try {
        // Table: scraping_rules (Adaptive Rules)
        await client.query(`
            CREATE TABLE IF NOT EXISTS scraping_rules (
                id SERIAL PRIMARY KEY,
                domain VARCHAR(255) UNIQUE NOT NULL,
                event_card_selector TEXT NOT NULL,
                title_selector TEXT NOT NULL,
                date_selector TEXT NOT NULL,
                location_selector TEXT,
                link_selector TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        `);

        // Table: activities (Events)
        await client.query(`
            CREATE TABLE IF NOT EXISTS activities (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                location TEXT,
                url TEXT UNIQUE NOT NULL,
                description TEXT,
                source_domain VARCHAR(255),
                raw_html TEXT,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        `);
        
        console.log('✅ Database tables initialized');
    } catch (err) {
        console.error('❌ Database initialization failed:', err);
    } finally {
        client.release();
    }
}

export default pool;
