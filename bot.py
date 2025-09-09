import os
import io
from flask import Flask, request
from pyrogram import Client
from pyrogram.types import Message
from PIL import Image

# ---------------- Config ----------------
API_ID = int(os.environ.get("API_ID", "21302239"))
API_HASH = os.environ.get("API_HASH", "1560930c983fbca6a1fcc8eab760d40d")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7649467838:AAFe8VrdrSCeJeEBYhZCjRpNw36jLRISiEQ")
PORT = int(os.environ.get("PORT", 5000))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://<your-render-service>.onrender.com/")

# ---------------- Flask App ----------------
flask_app = Flask(__name__)

# ---------------- Pyrogram Bot ----------------
app = Client(
    "RenamerBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ---------------- Memory Storage ----------------
user_files = {}     # {user_id: file_id}
user_thumbs = {}    # {user_id: BytesIO thumbnail}

# ---------------- Bot Handlers ----------------
@app.on_message()
async def all_messages(client: Client, message: Message):
    user_id = message.from_user.id

    # /start
    if message.text and message.text.lower() == "/start":
        await message.reply_text(
            "👋 Welcome! File bhejo, 1 sec me rename + thumbnail set kar dunga."
        )
        return

    # Photo → thumbnail
    if message.photo:
        photo_bytes = await message.download(file_name=io.BytesIO())
        photo_bytes.seek(0)
        img = Image.open(photo_bytes)
        img = img.convert("RGB")
        img.thumbnail((320, 320))
        thumb_bytes = io.BytesIO()
        img.save(thumb_bytes, format="JPEG")
        thumb_bytes.seek(0)
        user_thumbs[user_id] = thumb_bytes
        await message.reply_text("✅ Thumbnail saved!")
        return

    # File → ask new name
    if message.document or message.video or message.audio:
        file = message.document or message.video or message.audio
        file_name = file.file_name
        user_files[user_id] = file.file_id
        await message.reply_text(
            f"📂 File received: `{file_name}`\nSend new name with extension."
        )
        return

    # Text → rename + send
    if message.text and user_id in user_files:
        file_id = user_files.pop(user_id)
        new_name = message.text.strip()
        try:
            file_bytes = io.BytesIO()
            await client.download_media(file_id, file_bytes)
            file_bytes.seek(0)
            thumb = user_thumbs.get(user_id)
            await client.send_document(
                chat_id=message.chat.id,
                document=file_bytes,
                file_name=new_name,
                thumb=thumb,
                caption=f"✅ Renamed to `{new_name}`"
            )
        except Exception as e:
            await message.reply_text(f"❌ Error: {e}")
        return

# ---------------- Flask Route for Webhook ----------------
@flask_app.route("/", methods=["POST"])
def webhook():
    update = request.get_data()
    app.process_update(update)
    return "OK"

# ---------------- Main ----------------
if __name__ == "__main__":
    print("🚀 Renamer Bot Web Service Started...")
    flask_app.run(host="0.0.0.0", port=PORT)
