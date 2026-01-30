import os
import asyncio
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("echo-bot ready")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = update.message
    if m is None:
        return
    file_id = None
    if m.voice:
        file_id = m.voice.file_id
    elif m.audio:
        file_id = m.audio.file_id
    elif m.video_note:
        file_id = m.video_note.file_id
    if not file_id:
        return
    f = await context.bot.get_file(file_id)
    b = await f.download_as_bytearray()
    files = {"file": ("feedback.ogg", bytes(b))}
    try:
        r = requests.post(f"{BACKEND_URL}/api/analyze", files=files, timeout=30)
        data = r.json()
        score = data.get("score", "?")
        sentiment = data.get("sentiment", "?")
        keywords = data.get("keywords", [])
        ks = ", ".join(keywords) if isinstance(keywords, list) else str(keywords)
        await m.reply_text(f"score: {score}\nsentiment: {sentiment}\nkeywords: {ks}")
    except Exception:
        await m.reply_text("analyze failed")

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN missing")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO | filters.VIDEO_NOTE, handle_voice))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
