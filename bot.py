import os
from pyrogram import Client, filters
from pyrogram.types import Message
from flask import Flask
import threading

# Config
API_ID = int(os.environ.get("API_ID", "21302239"))
API_HASH = os.environ.get("API_HASH", "1560930c983fbca6a1fcc8eab760d40d")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8476510332:AAFiPdMnGGHUVYDxsjD8UoN5_ycfF6BjPh0")

app = Client(
    "RenamerBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ✅ Thumbnail storage per-user
user_thumbs = {}

# ---------- Start Command ----------
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    await message.reply_text(
        "👋 Welcome!\n\n"
        "📸 कोई image भेजो → वो तुम्हारा thumbnail बन जाएगा ✅\n"
        "📂 फिर कोई file/video भेजो → मैं rename करके उसी thumbnail के साथ भेज दूँगा 🚀"
    )

# ---------- Save Custom Thumbnail ----------
@app.on_message(filters.photo & filters.private)
async def save_thumb(client: Client, message: Message):
    user_id = message.from_user.id
    thumb_path = f"thumb_{user_id}.jpg"

    # Save thumb
    await message.download(file_name=thumb_path)
    user_thumbs[user_id] = thumb_path

    await message.reply_text("✅ Thumbnail saved! अब कोई video/file भेजो।")

# ---------- File Handler ----------
@app.on_message(filters.document | filters.video)
async def rename_instant(client: Client, message: Message):
    user_id = message.from_user.id
    file = message.document or message.video
    file_name = file.file_name

    # नया नाम (space → _)
    new_name = file_name.replace(" ", "_")

    try:
        # ✅ download file
        path = await client.download_media(message)
        new_path = os.path.join(os.getcwd(), new_name)
        os.rename(path, new_path)

        # ✅ check user thumbnail
        thumb = user_thumbs.get(user_id, None)

        # ✅ video के रूप में upload
        await message.reply_video(
            new_path,
            caption=f"✅ File renamed to `{new_name}`",
            thumb=thumb,
            supports_streaming=True
        )

        # cleanup
        os.remove(new_path)

    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# ---------- Flask Setup for Render ----------
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "✅ Renamer Video Bot (User Custom Thumbnail) is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port)

# ---------- Run both Flask + Pyrogram ----------
if __name__ == "__main__":
    print("🚀 Renamer Bot with User Thumbnail Started...")
    threading.Thread(target=run_flask).start()
    app.run()
