-- Upgrade Schema for EchoRank V2

-- 1. Modify activities table to support validation tags
ALTER TABLE activities 
ADD COLUMN IF NOT EXISTS validation_tags JSONB, -- Stores { "local": true, "web3": false, "co_creation": true }
ADD COLUMN IF NOT EXISTS validation_status BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS ai_summary TEXT;

-- 2. Create feedbacks table for storing voice feedback analysis
CREATE TABLE IF NOT EXISTS feedbacks (
    id SERIAL PRIMARY KEY,
    activity_id INTEGER REFERENCES activities(id),
    user_id VARCHAR(255), -- Telegram User ID or Web User ID
    user_handle VARCHAR(255),
    audio_url TEXT,
    transcription TEXT,
    sentiment_score FLOAT, -- Range: -1.0 to 1.0
    keywords JSONB, -- Array of strings ["awesome", "boring"]
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Create index for faster lookup by user and activity
CREATE INDEX IF NOT EXISTS idx_feedbacks_activity_id ON feedbacks(activity_id);
CREATE INDEX IF NOT EXISTS idx_feedbacks_user_id ON feedbacks(user_id);
