import os
from pyrogram import Client, filters
from pyrogram.types import Message
from flask import Flask
import threading

# Config
API_ID = int(os.environ.get("API_ID", "21302239"))   # my.telegram.org से
API_HASH = os.environ.get("API_HASH", "1560930c983fbca6a1fcc8eab760d40d")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8476510332:AAFiPdMnGGHUVYDxsjD8UoN5_ycfF6BjPh0")

app = Client(
    "RenamerBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ✅ Temporary dict for user files
user_files = {}

# Step 1: जब user file भेजे
@app.on_message(filters.document | filters.video | filters.audio)
async def ask_new_name(client: Client, message: Message):
    file = message.document or message.video or message.audio
    file_name = file.file_name

    await message.reply_text(
        f"📂 आपने भेजा है: `{file_name}`\n\n✏️ नया नाम भेजो (extension सही रखना, जैसे `.mp4`)"
    )

    # ✅ save file_id for rename step
    user_files[message.from_user.id] = file.file_id

# Step 2: नया नाम लेने के बाद
@app.on_message(filters.text & filters.private)
async def rename_file(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_files:
        return

    file_id = user_files.pop(user_id)
    new_name = message.text.strip()

    try:
        # download file
        path = await client.download_media(file_id)
        new_path = os.path.join(os.getcwd(), new_name)
        os.rename(path, new_path)

        # upload back
        await message.reply_document(new_path, caption=f"✅ File renamed to `{new_name}`")
        os.remove(new_path)
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# ---------- Flask Setup for Render ----------
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "✅ Renamer Bot is running on Render!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port)

# ---------- Run both Flask + Pyrogram ----------
if __name__ == "__main__":
    print("🚀 Renamer Bot Started...")
    threading.Thread(target=run_flask).start()
    app.run()
