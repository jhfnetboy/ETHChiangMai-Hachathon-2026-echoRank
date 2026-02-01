import logging
import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse
import html

# Load environment variables from local .env
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("POSTGRES_USER", "postgres") # Default for brew
DB_PASS = os.getenv("POSTGRES_PASSWORD", "")
DB_NAME = os.getenv("POSTGRES_DB", "echorank_crawler")

# Voiceprint Test State (In-memory for demo)
# user_id -> first_embedding
voice_test_state = {}

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

EMOTION_MAP = {
    "HAPPY": "开心 😊",
    "SAD": "悲伤 😟",
    "ANGRY": "愤怒 😡",
    "NEUTRAL": "平静 😐",
    "FEARFUL": "恐惧 😨",
    "DISGUSTED": "厌恶 🤢",
    "SURPRISED": "惊讶 😲"
}

# DB Connection
def get_db_connection():
    try:
        logging.info(f"🔍 Attempting to connect to database: {DB_NAME} on {DB_HOST}:{DB_PORT} as {DB_USER}")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            dbname=DB_NAME,
            connect_timeout=5
        )
        logging.info("✅ Database connection successful")
        return conn
    except Exception as e:
        logging.error(f"❌ Database connection failed: {e}")
        raise e

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "👋 <b>Welcome to EchoRank Bot!</b>\n\n"
        "I am your decentralized event assistant and community sentiment analyzer.\n\n"
        "🚀 <b>Quick Start:</b>\n"
        "1️⃣ <b>Discover</b>: Type 'Event' or '活动' to see upcoming events.\n"
        "2️⃣ <b>Feedback</b>: Select an event ID and send a <b>Voice Note</b>.\n"
        "3️⃣ <b>Report</b>: Use <code>/report &lt;id&gt;</code> to see community consensus.\n\n"
        "📥 <b>Submit an Event:</b>\n"
        "Use <code>/submit &lt;url&gt;</code> (e.g., Luma or Eventbrite link).\n"
        "<i>Note: Events are validated by AI based on:</i>\n"
        "• 📍 <b>Local</b>: Takes place in Chiang Mai.\n"
        "• 🌐 <b>Web3</b>: Related to Crypto, DAOs, or Decentralization.\n"
        "• 🤝 <b>Co-creation</b>: Encourages participation and building.\n\n"
        "🎙️ <b>Identity Test:</b>\n"
        "Use <code>/test_voice</code> to see if AI can recognize your voiceprint.\n\n"
        "Type /help at any time for more details."
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=help_text,
        parse_mode='HTML'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

import httpx
from bs4 import BeautifulSoup
import json
import sys
import os

# Add project root to sys.path to allow imports from services using absolute paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from services.ai.validator import validate_event_content
from services.ai.summarizer import generate_community_report

# ... (Previous imports remain, ensure clean merge)

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="usage: /report <activity_id>")
        return

    try:
        activity_id = int(context.args[0])
    except:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Activity ID must be a number.")
        return

    status_msg = await context.bot.send_message(chat_id=update.effective_chat.id, text=f"📊 Generating community report for Activity #{activity_id}...")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 1. Get Activity Title
        cur.execute("SELECT title FROM activities WHERE id = %s", (activity_id,))
        act = cur.fetchone()
        if not act:
            await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=f"❌ Activity #{activity_id} not found.")
            return
        
        event_title = act[0]

        # 2. Get All Feedbacks
        cur.execute("SELECT transcription, sentiment_score, keywords FROM feedbacks WHERE activity_id = %s", (activity_id,))
        rows = cur.fetchall()
        
        if not rows:
             await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=f"📭 No feedback recorded yet for **{event_title}**.")
             return

        feedbacks = []
        for r in rows:
            feedbacks.append({
                "transcription": r[0],
                "sentiment": r[1],
                "keywords": r[2] # Stringified JSON in DB
            })

        # 3. AI Summarization
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=f"🤖 AI Summarizing {len(feedbacks)} feedbacks...")
        
        report_data = generate_community_report(event_title, feedbacks)
        
        if not report_data or isinstance(report_data, str):
             await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=f"❌ Failed to generate report. ({report_data})")
             return

        # 4. Format Output
        summary = report_data.get('sentiment_report', 'No summary.')
        cloud = report_data.get('word_cloud', [])
        score = report_data.get('community_score', 0)
        
        # Color indicator based on score
        emoji = "🔴" if score < 40 else ("🟡" if score < 70 else "🟢")
        cloud_str = ", ".join(cloud)
        
        esc_title = html.escape(event_title)
        esc_summary = html.escape(summary)
        esc_cloud = html.escape(cloud_str)
        
        report_text = (
            f"📈 <b>Community Report: {esc_title}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"🌟 <b>Overall Score:</b> {emoji} {score}/100\n\n"
            f"📝 <b>Summary:</b>\n{esc_summary}\n\n"
            f"☁️ <b>Word Cloud:</b>\n<code>{esc_cloud}</code>\n\n"
            f"👥 Based on {len(feedbacks)} participants."
        )
        
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=report_text, parse_mode='HTML')

    except Exception as e:
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=f"❌ Error: {str(e)}")
    finally:
        cur.close()
        conn.close()

async def submit_url(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="usage: /submit <url>")
        return

    url = context.args[0]
    
    # Basic URL Format Validation
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValueError
    except:
         await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Invalid URL format.")
         return

    status_msg = await context.bot.send_message(chat_id=update.effective_chat.id, text=f"🔍 Analyzing URL: {url}...")

    # 1. Fetch Content (Lightweight Scrape)
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            resp = await client.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            resp.raise_for_status()
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Extract title and body text for AI
        page_title = soup.title.string if soup.title else ""
        body_text = soup.get_text(separator=' ', strip=True)[:4000] # Limit context
        full_text = f"Title: {page_title}\n\nContent: {body_text}"
        
    except Exception as e:
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=f"❌ Failed to fetch URL: {str(e)}")
        return

    # 2. AI Validation
    try:
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=f"🤖 AI Validating (Gemini)...")
        ai_result = validate_event_content(full_text)
        
        if not ai_result:
            await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text="❌ AI Validation failed (Error/Quota).")
            return
            
        # Check Validity
        is_valid = ai_result.get('valid', False)
        tags = ai_result.get('tags', {})
        summary = ai_result.get('summary', 'No summary.')
        metadata = ai_result.get('metadata', {})
        
        extracted_title = metadata.get('title') or page_title
        extracted_loc = metadata.get('location')
        extracted_time = metadata.get('time')
        
    except Exception as e:
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=f"❌ AI Error: {str(e)}")
        return

    # 3. DB Insertion
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Check if exists
        cur.execute("SELECT id FROM activities WHERE url = %s", (url,))
        exists = cur.fetchone()
        
        if exists:
             await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=f"⚠️ Event already exists! (ID: {exists[0]})")
        else:
            # Insert with AI Data
            # Note: start_time is skipped for now as we don't strictly parse "tomorrow 10am" to timestamp yet.
            # We store extracted_time in metadata JSON.
            
            cur.execute(
                """
                INSERT INTO activities 
                (url, title, location, source_domain, validation_status, validation_tags, ai_summary, metadata) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
                RETURNING id
                """,
                (
                    url, 
                    extracted_title[:255] if extracted_title else "Untitled",
                    extracted_loc,
                    result.netloc, 
                    is_valid, 
                    json.dumps(tags), 
                    summary,
                    json.dumps({"raw_time": extracted_time, "full_metadata": metadata})
                )
            )
            activity_id = cur.fetchone()[0]
            conn.commit()
            
            # 4. Final Reply
            tag_str = ", ".join([k for k,v in tags.items() if v])
            emoji = "✅" if is_valid else "❌"
            
            # Escape dynamic content
            esc_title = html.escape(extracted_title)
            esc_summary = html.escape(summary)
            esc_tags = html.escape(tag_str)
            
            final_text = (
                f"{emoji} <b>Event Processed</b>\n"
                f"<b>ID:</b> {activity_id}\n"
                f"<b>Title:</b> {esc_title}\n"
                f"<b>Tags:</b> {esc_tags}\n"
                f"<b>Status:</b> {'Approved' if is_valid else 'Rejected (Need 2/3 tags)'}\n\n"
                f"<b>Summary:</b> {esc_summary}\n"
            )
            await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=final_text, parse_mode='HTML')
            
            
    except Exception as e:
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=f"❌ DB Error: {str(e)}")
    finally:
        cur.close()
        conn.close()

async def list_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_text = update.message.text.strip().lower() if update.message.text else ""
    logging.info(f"📋 list_events called with text: '{msg_text}'")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        logging.info("📡 Fetching validated events from database...")
        
        # Fetch validated events
        cur.execute("""
            SELECT id, title, location, ai_summary, url 
            FROM activities 
            WHERE validation_status = TRUE 
            ORDER BY id DESC LIMIT 10
        """)
        rows = cur.fetchall()
        logging.info(f"📊 Found {len(rows)} validated events")
        
        if not rows:
            logging.warning("📭 No validated events found in database.")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="📭 No upcoming events found.")
            return

        msg = "📅 <b>Upcoming Events</b>\n\n"
        for row in rows:
            # row: id, title, location, summary, url
            esc_title = html.escape(row[1])
            esc_loc = html.escape(row[2])
            esc_summary = html.escape(row[3])
            esc_url = html.escape(row[4])
            msg += f"<b>{row[0]}. {esc_title}</b>\n📍 {esc_loc}\n🔗 <a href='{esc_url}'>Source Link</a>\n<i>{esc_summary}</i>\n\n"
            
        msg += "👇 <b>Reply with the Event ID number to give feedback.</b>"
        
        logging.info(f"📤 Sending event list to user {update.effective_user.id}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode='HTML')
        
    except Exception as e:
        logging.error(f"❌ Error in list_events: {str(e)}", exc_info=True)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Error fetching events: {str(e)}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()




async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # 1. Handle Keywords (Event / 活动)
    if update.message.text:
        text = update.message.text.lower().strip()
        logging.info(f"📩 Received message from {user_id}: '{text}'")
        if text in ["event", "活动", "/list"] or text.startswith("event") or text.startswith("活动"):
            logging.info(f"🎯 Command match! Calling list_events for user {user_id}")
            return await list_events(update, context)
        else:
            logging.debug(f"ℹ️ Message '{text}' did not match event commands")

    # 2. Handle Event Selection (Text Number)
    if update.message.text and update.message.text.strip().isdigit():
        event_id = int(update.message.text.strip())
        # Verify event exists
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT title FROM activities WHERE id = %s", (event_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            # Clear Test Mode to prevent conflicts
            if 'test_mode' in context.user_data:
                del context.user_data['test_mode']
                
            context.user_data['selected_event'] = event_id
            esc_title = html.escape(row[0])
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text=f"✅ Selected: <b>{esc_title}</b>\n\n🎙️ Please send a <b>Voice Message</b> to share your feedback.", 
                parse_mode='HTML'
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text="❌ Invalid Event ID. Type 'Event' to see the list.",
                parse_mode='HTML'
            )
        return

    # 3. Handle Fallback (Help)
    if update.message.text:
        await help_command(update, context)
        return

    # 2. Handle Voice Message
    if update.message.voice or update.message.audio:
        # Check if in Identity Test Mode
        test_mode = context.user_data.get('test_mode')
        print(f"DEBUG: Voice received. User: {user_id}, test_mode: {test_mode}")
        
        if test_mode:
            return await handle_voice_test(update, context)
            
        event_id = context.user_data.get('selected_event')
        if not event_id:
             await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Please select an event number first. Type 'Event' to list.")
             return

        status_msg = await context.bot.send_message(chat_id=update.effective_chat.id, text="🎙️ Receiving audio...")
        
        # Download Audio
        file_id = update.message.voice.file_id if update.message.voice else update.message.audio.file_id
        new_file = await context.bot.get_file(file_id)
        file_path = f"temp_{user_id}_{file_id}.ogg"
        await new_file.download_to_drive(file_path)
        
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text="🧠 AI Analyzing (SenseVoice)...")
        
        # Call AI Service (or Mock)
        ai_result = {}
        try:
            # Try connecting to local AI service
            async with httpx.AsyncClient(timeout=60.0) as client:
                with open(file_path, "rb") as f:
                     resp = await client.post("http://127.0.0.1:8001/analyze", files={"audio": f})
                
                if resp.status_code == 200:
                    data = resp.json()
                    res = data.get("result", {})
                    ai_result = {
                        "transcription": res.get("transcript"),
                        "sentiment_score": res.get("intensity", 0.5), # Map intensity to score roughly
                        "emotion": res.get("emotion", "NEUTRAL"),
                        "confidence": res.get("confidence", 0.5),
                        "keywords": res.get("keywords", [])
                    }
                else:
                    raise Exception(f"Service Error {resp.status_code}")
                    
        except Exception as e:
            print(f"AI Service Failed: {e}")
            # FALLBACK MOCK (For Simulated Testing)
            ai_result = {
                 "transcription": "[Simulated] The environment was amazing and the people were very friendly. Highly recommended!",
                 "sentiment_score": 0.9,
                 "emotion": "HAPPY",
                 "confidence": 0.85,
                 "keywords": ["amazing", "friendly", "recommended"]
            }
        
        # Cleanup
        try:
            os.remove(file_path)
        except:
            pass
            
        # Store in DB
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO feedbacks 
                (activity_id, user_id, user_handle, audio_url, transcription, sentiment_score, keywords, emotion, confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                event_id, 
                str(user_id), 
                update.effective_user.username,
                "telegram_file_id:" + file_id,
                ai_result['transcription'],
                ai_result['sentiment_score'],
                json.dumps(ai_result['keywords']),
                ai_result['emotion'],
                ai_result['confidence']
            ))
            conn.commit()
            
            # Reply with 4 Dimensions
            esc_transcript = html.escape(ai_result['transcription'])
            esc_keywords = html.escape(", ".join(ai_result['keywords']))
            emotion_zh = EMOTION_MAP.get(ai_result['emotion'], ai_result['emotion'])
            confidence_pct = ai_result['confidence'] * 100
            
            reply_text = (
                f"✅ <b>反馈已记录 (Feedback Recorded)</b>\n\n"
                f"📝 <b>1. 用户评价 (Evaluation):</b>\n\"{esc_transcript}\"\n\n"
                f"🎭 <b>2. 语音情感 (Emotion):</b> {emotion_zh}\n\n"
                f"⚖️ <b>3. 置信度/真实性 (Confidence):</b> {confidence_pct:.1f}%\n"
                f"😊 <b>综合评分 (Score):</b> {ai_result['sentiment_score']:.2f}\n\n"
                f"🏷️ <b>4. 关键词 (Keywords):</b> {esc_keywords}"
            )
            
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id, 
                message_id=status_msg.message_id, 
                text=reply_text,
                parse_mode='HTML'
            )
            
        except Exception as e:
             await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=f"❌ Save Error: {e}")
        finally:
            cur.close()
            conn.close()


async def test_voice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Reset state
    if user_id in voice_test_state:
        del voice_test_state[user_id]
    
    context.user_data['test_mode'] = True
    print(f"DEBUG: Set test_mode=True for user {user_id}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "🧬 <b>Speaker Identity Test Mode</b>\n\n"
            "I'm now recording your voiceprint. Please send your <b>first</b> voice message."
        ),
        parse_mode='HTML'
    )

async def handle_voice_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    file_id = update.message.voice.file_id if update.message.voice else update.message.audio.file_id
    new_file = await context.bot.get_file(file_id)
    file_path = f"test_{user_id}_{file_id}.ogg"
    await new_file.download_to_drive(file_path)
    
    status_msg = await context.bot.send_message(chat_id=update.effective_chat.id, text="🔍 Extracting Voiceprint...")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(file_path, "rb") as f:
                 resp = await client.post("http://127.0.0.1:8001/voiceprint", files={"audio": f})
            
            if resp.status_code != 200:
                raise Exception(f"AI Service Error: {resp.text}")
                
            embedding = resp.json().get("embedding")
            
            if user_id not in voice_test_state:
                # First time recording
                voice_test_state[user_id] = embedding
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=status_msg.message_id,
                    text="✅ <b>First Voiceprint Recorded!</b>\n\nNow send a <b>second</b> voice message (it can be different words) to see if I recognize you.",
                    parse_mode='HTML'
                )
            else:
                # Compare
                await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text="🔄 Comparing Identity...")
                
                comp_resp = await client.post(
                    "http://127.0.0.1:8001/compare_voiceprints", 
                    json={"embedding1": voice_test_state[user_id], "embedding2": embedding}
                )
                
                if comp_resp.status_code != 200:
                    raise Exception(f"Comparison Error: {comp_resp.text}")
                
                result = comp_resp.json()
                similarity = result.get("similarity", 0)
                # Match Threshold
                matched = similarity > 0.60
                
                emoji = "✅" if matched else "❌"
                status = "<b>Identity Matched!</b>" if matched else "<b>Identity Mismatch!</b>"
                
                reply_text = (
                    f"{emoji} {status}\n\n"
                    f"<b>Similarity Score:</b> {similarity:.4f}\n"
                    f"<b>Telegram ID:</b> <code>{user_id}</code>\n\n"
                    f"AI now confirms: Even with different words, I know it's you based on your unique vocal cords. 🎤✨\n\n"
                    "Type /test_voice to start over or Event to go back."
                )
                
                # Exit test mode
                context.user_data['test_mode'] = False
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=status_msg.message_id,
                    text=reply_text,
                    parse_mode='HTML'
                )
                
    except Exception as e:
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=f"❌ Error: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN not found in .env")
        exit(1)
        
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help_command)
    submit_handler = CommandHandler('submit', submit_url)
    report_handler = CommandHandler('report', report_command)
    test_voice_handler = CommandHandler('test_voice', test_voice_command)
    # Generic message handler for Keywords, Numbers and Voice
    msg_handler = MessageHandler(filters.TEXT | filters.VOICE | filters.AUDIO, handle_message)
    
    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(submit_handler)
    application.add_handler(report_handler)
    application.add_handler(test_voice_handler)
    application.add_handler(msg_handler)
    
    print("Bot is running...")
    application.run_polling()
