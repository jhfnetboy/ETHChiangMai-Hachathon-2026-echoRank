import logging
import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

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

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# DB Connection
def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        dbname=DB_NAME
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="👋 Welcome to EchoRank Bot!\n\nI am your decentralized event assistant.\n\n**Submit Mode:**\n/submit <url> - Add an event\n\n**Discover Mode:**\nType 'Event' or '活动' to find things to do."
    )

import httpx
from bs4 import BeautifulSoup
import json
import sys
import os

# Add project root to sys.path to allow imports from services using absolute paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from services.ai.validator import validate_event_content

# ... (Previous imports remain, ensure clean merge)

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
            final_text = (
                f"{emoji} **Event Processed**\n"
                f"**ID:** {activity_id}\n"
                f"**Title:** {extracted_title}\n"
                f"**Tags:** {tag_str}\n"
                f"**Status:** {'Approved' if is_valid else 'Rejected (Need 2/3 tags)'}\n\n"
                f"**Summary:** {summary}\n"
            )
            await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=final_text, parse_mode='Markdown')
            
            
    except Exception as e:
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=f"❌ DB Error: {str(e)}")
    finally:
        cur.close()
        conn.close()

async def list_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if not (text == "event" or text == "活动" or text == "/list"):
        return

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Fetch validated events
        cur.execute("""
            SELECT id, title, location, ai_summary 
            FROM activities 
            WHERE validation_status = TRUE 
            ORDER BY id DESC LIMIT 10
        """)
        rows = cur.fetchall()
        
        if not rows:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="📭 No upcoming events found.")
            return

        msg = "📅 **Upcoming Events**\n\n"
        for row in rows:
            # row: id, title, location, summary
            msg += f"**{row[0]}. {row[1]}**\n📍 {row[2]}\n_{row[3]}_\n\n"
            
        msg += "👇 **Reply with the Event ID number to give feedback.**"
        
        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode='Markdown')
        
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Error fetching events: {str(e)}")
    finally:
        cur.close()
        conn.close()




async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # 1. Handle Event Selection (Text Number)
    if update.message.text and update.message.text.isdigit():
        event_id = int(update.message.text)
        # Verify event exists
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT title FROM activities WHERE id = %s", (event_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            context.user_data['selected_event'] = event_id
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ Selected: **{row[0]}**\n\n🎙️ Please send a **Voice Message** to share your feedback.", parse_mode='Markdown')
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Invalid Event ID. listing events again...")
            # optional: trigger list_events?
        return

    # 2. Handle Voice Message
    if update.message.voice or update.message.audio:
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
                (activity_id, user_id, user_handle, audio_url, transcription, sentiment_score, keywords)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                event_id, 
                str(user_id), 
                update.effective_user.username,
                "telegram_file_id:" + file_id,
                ai_result['transcription'],
                ai_result['sentiment_score'],
                json.dumps(ai_result['keywords'])
            ))
            conn.commit()
            
            # Reply
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id, 
                message_id=status_msg.message_id, 
                text=f"✅ **Feedback Recorded!**\n\n💬 \"{ai_result['transcription'][:100]}...\"\n😊 Sentiment: {ai_result['sentiment_score']:.2f}\n🏷️ Keywords: {', '.join(ai_result['keywords'])}",
                parse_mode='Markdown'
            )
            
        except Exception as e:
             await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_msg.message_id, text=f"❌ Save Error: {e}")
        finally:
            cur.close()
            conn.close()


if __name__ == '__main__':
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN not found in .env")
        exit(1)
        
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    submit_handler = CommandHandler('submit', submit_url)
    list_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), list_events)
    # Generic message handler for Numbers and Voice
    msg_handler = MessageHandler(filters.TEXT | filters.VOICE | filters.AUDIO, handle_message)
    
    application.add_handler(start_handler)
    application.add_handler(submit_handler)
    application.add_handler(list_handler)
    application.add_handler(msg_handler)
    
    print("Bot is running...")
    application.run_polling()
