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

# ✅ Thumbnail path (एक बार set कर ले)
THUMB_PATH = "thumb.jpg"   # कोई भी jpg/png file रख सकता है

# ---------- Start Command ----------
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    await message.reply_text(
        "👋 Welcome!\n\n"
        "📂 बस कोई file भेजो, मैं 1 sec में rename करके thumbnail लगा कर भेज दूँगा ✅"
    )

# ---------- File Handler ----------
@app.on_message(filters.document | filters.video | filters.audio)
async def rename_instant(client: Client, message: Message):
    file = message.document or message.video or message.audio
    file_name = file.file_name

    # नया नाम बना लो (example: space replace with _)
    new_name = file_name.replace(" ", "_")

    try:
        # ✅ download file
        path = await client.download_media(message)
        new_path = os.path.join(os.getcwd(), new_name)
        os.rename(path, new_path)

        # ✅ अगर thumbnail मौजूद है तो attach कर
        thumb = THUMB_PATH if os.path.exists(THUMB_PATH) else None

        # ✅ upload back
        await message.reply_document(
            new_path,
            caption=f"✅ File renamed to `{new_name}`",
            thumb=thumb
        )

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
