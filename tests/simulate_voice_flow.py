import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from services.bot.bot import handle_message, get_db_connection

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
        self.bot = AsyncMock()
        self.bot.get_file = AsyncMock()
        self.bot.get_file.return_value.download_to_drive = AsyncMock()

async def run_simulation():
    print("🚀 Starting Simulation...")
    
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
    
    # Verify Session State
    if context.user_data.get('selected_event') == event_id:
        print("   ✅ Session state updated correctly.")
    else:
        print(f"   ❌ Session state failed! {context.user_data}")
        return

    # Verify Reply
    context.bot.send_message.assert_called()
    print("   ✅ Bot replied to selection.")

    # 3. Simulate User Sending Voice
    print("\n[Step 3] User sends voice...")
    
    # Create dummy voice object
    voice_file = MagicMock()
    voice_file.file_id = "mock_voice_file_id"
    update_voice = MockUpdate(MockMessage(voice=voice_file))
    
    # Mock download behavior (touch file)
    async def mock_download(path):
        with open(path, 'wb') as f:
            f.write(b'OggS') # Dummy header
    context.bot.get_file.return_value.download_to_drive = mock_download
    
    # Run Handler
    await handle_message(update_voice, context)
    
    # 4. Verify DB Insertion
    print("\n[Step 4] Verifying DB feedback...")
    cur.execute("SELECT sentiment_score, keywords FROM feedbacks WHERE user_id = '123456789' ORDER BY id DESC LIMIT 1")
    feedback = cur.fetchone()
    
    if feedback:
        print(f"   ✅ Feedback found! Sentiment: {feedback[0]}, Keywords: {feedback[1]}")
    else:
        print("   ❌ No feedback found in DB!")

    # Cleanup
    cur.execute("DELETE FROM feedbacks WHERE user_id = '123456789'")
    cur.execute("DELETE FROM activities WHERE id = %s", (event_id,))
    conn.commit()
    cur.close()
    conn.close()
    
    print("\n✅ Simulation Complete!")

if __name__ == "__main__":
    asyncio.run(run_simulation())
