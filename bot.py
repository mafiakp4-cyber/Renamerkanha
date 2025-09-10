import os
import threading
from pyrogram import Client, filters
from pyrogram.types import Message
from flask import Flask

# Config (Environment Variables से)
API_ID = int(os.environ.get("API_ID", "21302239"))
API_HASH = os.environ.get("API_HASH", "1560930c983fbca6a1fcc8eab760d40d")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8476510332:AAFiPdMnGGHUVYDxsjD8UoN5_ycfF6BjPh0")

app = Client(
    "ThumbChangerBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# User thumbnails store
user_thumbs = {}

# Step 1: जब user कोई photo भेजे (thumbnail सेट करने के लिए)
@app.on_message(filters.photo & filters.private)
async def save_thumb(client: Client, message: Message):
    photo = message.photo.file_id
    user_thumbs[message.from_user.id] = photo
    await message.reply_text("✅ Thumbnail सेट हो गया!\nअब MP4 video भेजो।")

# Step 2: जब user कोई MP4 video भेजे
@app.on_message(filters.video & filters.private)
async def change_thumb(client: Client, message: Message):
    user_id = message.from_user.id
    video = message.video
    file_name = video.file_name

    # ✅ सिर्फ mp4 files allow
    if not file_name.lower().endswith(".mp4"):
        await message.reply_text("❌ सिर्फ MP4 videos allowed हैं!")
        return

    thumb = user_thumbs.get(user_id)
    status = await message.reply_text("⏳ Processing...")

    try:
        await client.send_video(
            chat_id=message.chat.id,
            video=video.file_id,
            file_name=file_name,
            thumb=thumb,
            caption=f"✅ Thumbnail changed!"
        )
        await status.edit("✅ Done! Thumbnail changed successfully.")
    except Exception as e:
        await status.edit(f"❌ Error: {e}")

print("🚀 Thumbnail Changer Bot Started...")

# Dummy Flask app for Render
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "✅ Thumbnail Changer Bot is running on Render!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port)

# Thread में दोनों parallel चलेंगे
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    app.run()
