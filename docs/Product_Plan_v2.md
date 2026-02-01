# Product Plan v2: EchoRank (Hackathon Pivot)

## 1. Core Philosophy
**"Decentralized Event Feedback & Co-creation"**
We divide users into two distinct flows based on their intent/reputation.

## 2. User Personas & Workflows

### A. The Submitter (High Reputation / Project Owner)
*Target: Event Organizers, Hackathon Builders.*
*Goal: Input event data into the system for indexation.*

**Workflow:**
1.  **Input:** User submits an Event Activity URL via **Web Interface** or **Telegram Bot** command (e.g., `/submit <url>`).
2.  **Processing (AI Agent):**
    *   Crawler extracts content from URL.
    *   AI analyzes content against **3 Criteria** (Must meet 2/3):
        1.  **Chiang Mai Local**: Is it happening physically in Chiang Mai?
        2.  **Web3/Crypto**: Is it related to Blockchain, ETH, Crypto?
        3.  **Co-creation/Academic**: Is it about learning, workshops, humanities, or academic discussion? (Not just pure partying/shilling).
3.  **Output:**
    *   **Pass:** Event is saved to Database. Bot/Web replies "Success: Event [Name] added."
    *   **Fail:** Bot/Web replies "Failed: [Reason] (e.g., Only matches 1/3 criteria)."

### B. The Participant (General Audience)
*Target: Attendees, Tourists, Hackers.*
*Goal: Discover events and provide authentic feedback.*

**Workflow:**
1.  **Discovery:**
    *   User says keyword **"Event"** or **"活动"** to Bot.
    *   Bot returns a numbered list of *Upcoming/Recent* events.
        > 1. ETH Chiang Mai Opening (Today 10:00)
        > 2. Luma Developer Workshop (Today 14:00)
2.  **Selection:** User replies with Number (e.g., "1").
3.  **Feedback:**
    *   Bot prompts: "Please send a voice message sharing your thoughts."
    *   User records **Voice Message**.
4.  **Analysis (AI Agent):**
    *   STT (Speech-to-Text) converts voice to text.
    *   AI extracts **Keywords** and performs **Sentiment Analysis**.
    *   Feedback is linked to the Event ID.
5.  **Report:**
    *   System aggregates feedback to generate a **Word Cloud** and **Sentiment Summary** for the event.

## 3. Technical Architecture

### Services
1.  **Telegram Bot (`services/bot`)**: Interface for both Submitter and Participant.
2.  **Crawler Service (`services/crawler`)**:
    *   Fetches URL content for Submitters.
    *   Manages PostgreSQL Database.
3.  **AI Service (`services/ai`)**:
    *   **Validator Agent:** Checks 2/3 criteria.
    *   **Feedback Agent:** Transcribes audio (Whisper), extracts keywords, analyzes sentiment.

### Data Storage
*Preference: PostgreSQL (since it's already set up in Crawler).*
*Fallback: JSON (if strictly requested, but DB is cleaner).*

**Schema Updates:**
*   `activities`: Add `tags` (JSON), `validation_status` (Boolean), `ai_summary`.
*   `feedbacks`: New table.
    *   `id`, `activity_id`, `user_id`, `audio_url`, `transcription`, `sentiment_score`, `keywords` (JSON).

## 4. Implementation Steps

### Phase 1: Event Submission & Validation (The "Filter")
- [ ] Update Bot to handle `/submit <url>`.
- [ ] Implement `ValidatorAgent` in AI Service (Prompt: "Analyze this text for [Tags]. Return JSON boolean").
- [ ] Connect Bot -> Crawler/AI -> DB.

### Phase 2: Discovery & Interaction (The "Loop")
- [ ] Update Bot to capture "Event" keyword and query DB for active events.
- [ ] Implement Session State in Bot (User selected Event #1, waiting for audio).
- [ ] Handle Voice Message -> Send to AI Service.

### Phase 3: Analysis & Reporting (The "Cloud")
- [ ] Implement STT (Whisper or API).
- [ ] Generate Word Cloud (Python `wordcloud` lib or frontend visualization).
- [ ] Display Report (Text summary in simple Bot response).
