import os
import threading
from pyrogram import Client, filters
from pyrogram.types import Message
from flask import Flask

# Config
API_ID = int(os.environ.get("API_ID", "21302239"))   # my.telegram.org से
API_HASH = os.environ.get("API_HASH", "1560930c983fbca6a1fcc8eab760d40d")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7649467838:AAFe8VrdrSCeJeEBYhZCjRpNw36jLRISiEQ")

app = Client(
    "RenamerBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Memory storage
user_files = {}
user_thumbs = {}

# Flask app for Render
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "✅ Renamer Bot is running on Render!"

# /start command
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    await message.reply_text(
        "👋 *Welcome to Renamer Bot!*\n\n"
        "📂 कोई भी file/video भेजो → मैं rename कर दूँगा ✅\n"
        "🖼️ कोई भी image भेजो → वो thumbnail set हो जाएगी instantly 🚀",
        quote=True
    )

# Save thumbnail
@app.on_message(filters.photo & filters.private)
async def save_thumb(client: Client, message: Message):
    user_id = message.from_user.id
    thumb_path = await message.download()
    user_thumbs[user_id] = thumb_path
    await message.reply_text("✅ Thumbnail saved! अब कोई video/file भेजो।", quote=True)

# Ask new name
@app.on_message((filters.document | filters.video | filters.audio) & filters.private)
async def ask_new_name(client: Client, message: Message):
    file = message.document or message.video or message.audio
    file_name = file.file_name
    await message.reply_text(
        f"📂 आपने भेजा:\n`{file_name}`\n\n✏️ नया नाम भेजो (extension मत भूलना, जैसे `.mp4`)",
        quote=True
    )
    user_files[message.from_user.id] = file.file_id

# Rename + send back
@app.on_message(filters.text & filters.private)
async def rename_file(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_files:
        return
    file_id = user_files.pop(user_id)
    new_name = message.text.strip()

    try:
        path = await client.download_media(file_id)
        new_path = os.path.join(os.getcwd(), new_name)
        os.rename(path, new_path)

        thumb = user_thumbs.get(user_id)

        await message.reply_document(
            new_path,
            caption=f"✅ File renamed to `{new_name}`",
            thumb=thumb
        )
        os.remove(new_path)
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# Run Flask + Pyrogram together
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("🚀 Renamer Bot Started on Render!")
    app.run()
