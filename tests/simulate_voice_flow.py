import asyncio
import os
import sys
import json
from unittest.mock import AsyncMock, MagicMock
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from services.bot.bot import handle_message, get_db_connection, report_command

# Mock Classes for Telegram Objects
class MockUser:
    id = 123456789
    username = "test_user"

class MockChat:
    id = 987654321

class MockMessage:
    def __init__(self, text=None, voice=None):
        self.text = text
        self.voice = voice
        self.audio = voice # Treat voice/audio same for this test
        self.message_id = 111

class MockUpdate:
    def __init__(self, message):
        self.message = message
        self.effective_user = MockUser()
        self.effective_chat = MockChat()

class MockContext:
    def __init__(self):
        self.user_data = {}
        self.args = []
        self.bot = AsyncMock()
        self.bot.get_file = AsyncMock()
        self.bot.get_file.return_value.download_to_drive = AsyncMock()
        self.bot.send_message = AsyncMock()
        self.bot.edit_message_text = AsyncMock()

async def run_simulation():
    print("🚀 Starting Simulation V2...")
    
    # 1. Setup DB with dummy event
    print("\n[Step 1] Setting up dummy data...")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO activities (title, url, validation_status) VALUES ('Simulated Event', 'http://mock', TRUE) ON CONFLICT DO NOTHING RETURNING id")
    row = cur.fetchone()
    if not row:
        cur.execute("SELECT id FROM activities WHERE title = 'Simulated Event'")
        event_id = cur.fetchone()[0]
    else:
        event_id = row[0]
    conn.commit()
    print(f"   Target Event ID: {event_id}")

    # 2. Simulate User Selecting Event
    print("\n[Step 2] User selects event...")
    context = MockContext()
    update_select = MockUpdate(MockMessage(text=str(event_id)))
    await handle_message(update_select, context)
    
    if context.user_data.get('selected_event') == event_id:
        print("   ✅ Session state updated.")
    
    # 3. Simulate User Sending Voice
    print("\n[Step 3] User sends voice...")
    voice_file = MagicMock()
    voice_file.file_id = "mock_voice_file_id"
    update_voice = MockUpdate(MockMessage(voice=voice_file))
    
    async def mock_download(path):
        with open(path, 'wb') as f: f.write(b'OggS')
    context.bot.get_file.return_value.download_to_drive = mock_download
    
    await handle_message(update_voice, context)
    
    # 4. Verify DB Insertion
    print("\n[Step 4] Verifying DB feedback...")
    cur.execute("SELECT transcription FROM feedbacks WHERE user_id = '123456789' ORDER BY id DESC LIMIT 1")
    feedback = cur.fetchone()
    if feedback:
        print(f"   ✅ Feedback stored: {feedback[0][:30]}...")

    # 5. Simulate /report Command
    print("\n[Step 5] Simulating /report command...")
    update_report = MockUpdate(MockMessage())
    context_report = MockContext()
    context_report.args = [str(event_id)]
    
    await report_command(update_report, context_report)
    
    # Check if edit_message_text was called with a report
    args, kwargs = context_report.bot.edit_message_text.call_args
    if "Community Report" in kwargs.get('text', ''):
        print("   ✅ Report generated successfully.")
    else:
        print(f"   ❌ Report failed! Output: {kwargs.get('text')}")

    # Cleanup
    print("\n[Cleaning up]...")
    cur.execute("DELETE FROM feedbacks WHERE user_id = '123456789'")
    cur.execute("DELETE FROM activities WHERE id = %s", (event_id,))
    conn.commit()
    cur.close()
    conn.close()
    
    print("\n✅ Simulation V2 Complete!")

if __name__ == "__main__":
    asyncio.run(run_simulation())
