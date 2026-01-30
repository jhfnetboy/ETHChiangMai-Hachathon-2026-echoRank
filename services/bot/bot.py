import os
import asyncio
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
BOT_NAME = os.getenv("BOT_NAME", "echoRankBot")
TELE_URL = os.getenv("Tele_URL", "")
INTRO_MSG = "echoRank is a Event Echo Tool, which powerd by Decentralized Community AI. More informain here: https://github.com/jhfnetboy/ETHChiangMai-Hachathon-2026-echoRank"
INSTR_MSG = (
    "👋 欢迎使用 echoRank bot\n"
    "使用方式：请按住对话框右侧的麦克风说话；后台 AI 返回分析结果并自动上链；务必提及你反馈的活动名称，否则反馈无效。\n"
    "EN: Welcome to echoRank bot.\n"
    "Press the microphone button to speak. AI will analyze and record on-chain.\n"
    "Please mention the event name, otherwise feedback is invalid."
)
LAST_ACTIVITY: dict[int, tuple[str, float]] = {}
STATUS_PORT = int(os.getenv("BOT_STATUS_PORT", "8081"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"{BOT_NAME} ready"
    if TELE_URL:
        msg += f" ({TELE_URL})"
    await update.message.reply_text(msg)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = update.message
    if not m or not m.text:
        return
    chat_type = update.effective_chat.type if update.effective_chat else ""
    text_lower = m.text.lower()
    bot_un = (context.bot.username or BOT_NAME).lower()
    mentioned = f"@{bot_un}" in text_lower or BOT_NAME.lower() in text_lower
    if chat_type == "private":
        # 记录最近活动名（简单起见，使用整段文本）
        if update.effective_user and m.text:
            LAST_ACTIVITY[update.effective_user.id] = (m.text.strip(), __import__("time").time())
        await m.reply_text(INSTR_MSG)
        return
    # group/supergroup: only respond when mentioned
    if mentioned or ("/help" in text_lower and mentioned) or ("help" in text_lower and mentioned):
        await m.reply_text(INSTR_MSG)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = update.message
    if m is None:
        return
    chat_type = update.effective_chat.type if update.effective_chat else ""
    # group/supergroup: ignore voice
    if chat_type != "private":
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
    user_id = update.effective_user.id if update.effective_user else 0
    window_ms = 10 * 60 * 1000
    import time as _t
    bucket = int(_t.time() * 1000) // window_ms * window_ms
    session_id = f"{user_id}-{bucket}"
    activity_name = ""
    if user_id in LAST_ACTIVITY:
        activity_name = LAST_ACTIVITY[user_id][0]
    try:
        r = requests.post(
            f"{BACKEND_URL}/api/analyze",
            files=files,
            data={"session_id": session_id, "user_id": str(user_id), "activity_name": activity_name},
            timeout=30
        )
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
    # Ensure event loop exists for Python 3.14+
    try:
        import asyncio
        asyncio.get_event_loop()
    except Exception:
        import asyncio
        asyncio.set_event_loop(asyncio.new_event_loop())
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", handle_text))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO | filters.VIDEO_NOTE, handle_voice))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class StatusHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != "/status":
                self.send_response(404)
                self.end_headers()
                return
            payload = (
                '{"service":"bot","ok":true,"name":"%s","link":"%s"}'
                % (BOT_NAME, TELE_URL)
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload.encode("utf-8"))

    def start_status_server():
        try:
            srv = HTTPServer(("0.0.0.0", STATUS_PORT), StatusHandler)
            srv.serve_forever()
        except Exception:
            pass

    t = threading.Thread(target=start_status_server, daemon=True)
    t.start()
    main()
