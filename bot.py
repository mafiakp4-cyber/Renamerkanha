import os
import asyncio
import threading
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = int(os.getenv("API_ID", "21302239"))
API_HASH = os.getenv("API_HASH", "1560930c983fbca6a1fcc8eab760d40d")
BOT_TOKEN = os.getenv("8020112693:AAGjbPsjdgLVUrasto0AeJ-Fht121MKOpwQ")

bot = Client("thumb_renamer", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "✅ Bot is running on Render!"

# 🔹 Thumbnail Save
@bot.on_message(filters.photo & filters.private)
async def save_thumb(_, message: Message):
    path = await message.download(file_name="thumb.jpg")
    await message.reply_text("✅ Thumbnail saved successfully!\nअब कोई video/file भेजो 📁")

# 🔹 Start Command
@bot.on_message(filters.command("start") & filters.private)
async def start(_, message: Message):
    await message.reply_text(
        "👋 Welcome!\nबस कोई file भेजो, मैं 1 sec में rename करके thumbnail लगा दूँ ✅"
    )

# 🔹 File / Video Rename + Thumb Apply
@bot.on_message(filters.document | filters.video)
async def rename_and_send(_, message: Message):
    if not os.path.exists("thumb.jpg"):
        await message.reply_text("❌ पहले कोई thumbnail photo भेजो!")
        return
    
    file_path = await message.download()
    file_name = os.path.basename(file_path)
    await message.reply_text("⚙️ Processing... Thumbnail apply हो रहा है 🔄")

    try:
        await message.reply_video(
            video=file_path,
            thumb="thumb.jpg",
            caption=f"✅ Done! Thumbnail updated!\n📁 File: {file_name}",
        )
        os.remove(file_path)
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# 🔹 Run Flask + Bot together
def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("🚀 Bot Started Successfully on Render")
    asyncio.get_event_loop().run_until_complete(bot.start())
    asyncio.get_event_loop().run_forever()
