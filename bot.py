import os
import threading
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import Message

# 🔑 Config (Environment Variables से)
API_ID = int(os.environ.get("API_ID", "21302239"))
API_HASH = os.environ.get("API_HASH", "1560930c983fbca6a1fcc8eab760d40d")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7649467838:AAFe8VrdrSCeJeEBYhZCjRpNw36jLRISiEQ")

app = Client(
    "FastRenamerBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Temporary storage
user_files = {}
user_thumbs = {}

# ✅ Start command
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    await message.reply_text(
        "👋 Welcome!\n\n"
        "📸 कोई *image* भेजो → Thumbnail set हो जाएगा ✅\n"
        "📂 फिर कोई *video/file* भेजो → मैं उसे rename करके उसी Thumbnail के साथ भेज दूँगा 🚀"
    )

# ✅ Thumbnail save
@app.on_message(filters.photo & filters.private)
async def save_thumbnail(client: Client, message: Message):
    user_thumbs[message.from_user.id] = message.photo.file_id
    await message.reply_text("✅ Thumbnail saved! अब कोई video/file भेजो।")

# ✅ File receive
@app.on_message(filters.document | filters.video | filters.audio)
async def ask_new_name(client: Client, message: Message):
    file = message.document or message.video or message.audio
    file_name = file.file_name

    await message.reply_text(
        f"📂 आपने भेजा है:\n`{file_name}`\n\n✏️ नया नाम भेजो "
        f"(extension मत भूलना, जैसे `.mp4`)"
    )

    user_files[message.from_user.id] = file.file_id

# ✅ Fast Rename (Direct from Telegram server)
@app.on_message(filters.text & filters.private)
async def fast_rename(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_files:
        return

    file_id = user_files.pop(user_id)
    new_name = message.text.strip()
    thumb = user_thumbs.get(user_id)

    try:
        await client.send_document(
            chat_id=message.chat.id,
            document=file_id,
            file_name=new_name,
            thumb=thumb,
            caption=f"✅ File renamed to `{new_name}`"
        )
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

print("🚀 Fast Renamer Bot Started...")

# Dummy Flask app (for Render)
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "✅ Fast Renamer Bot is running on Render!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    app.run()
