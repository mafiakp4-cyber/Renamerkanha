import os
import threading
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import Message

# 🔧 Config
API_ID = int(os.environ.get("API_ID", "21302239"))
API_HASH = os.environ.get("API_HASH", "1560930c983fbca6a1fcc8eab760d40d")
BOT_TOKEN = os.environ.get("8020112693:AAGjbPsjdgLVUrasto0AeJ-Fht121MKOpwQ")

bot = Client("fast_renamer", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
flask_app = Flask(__name__)

# 🟢 Flask for Render
@flask_app.route('/')
def home():
    return "✅ Fast Renamer Bot is running on Render!"

# 🟢 /start command
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(_, message: Message):
    await message.reply_text(
        "👋 **Welcome to Fast Renamer Bot!**\n\n"
        "📸 Send me a thumbnail first.\n📂 Then send any video — I'll rename & set thumbnail instantly ⚡"
    )

# 🟢 Save thumbnail
@bot.on_message(filters.photo & filters.private)
async def save_thumb(_, message: Message):
    thumb_path = await message.download(file_name="thumb.jpg")
    await message.reply_text("✅ Thumbnail saved successfully! अब कोई video भेजो 🎥")

# 🟢 Handle video / file rename
@bot.on_message(filters.video | filters.document)
async def rename_video(_, message: Message):
    if not os.path.exists("thumb.jpg"):
        await message.reply_text("❌ पहले thumbnail भेजो!")
        return

    video_path = await message.download()
    await message.reply_text("⚙️ Processing thumbnail... 🔄")

    try:
        await message.reply_video(
            video=video_path,
            thumb="thumb.jpg",
            caption="✅ Thumbnail changed successfully in 1 second ⚡"
        )
        os.remove(video_path)
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# 🧩 Flask Run Thread
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

# 🧩 Main Run
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("🚀 Bot started successfully on Render!")
    bot.run()
