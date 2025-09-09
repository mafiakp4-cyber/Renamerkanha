import os
import tempfile
from flask import Flask, request
from pyrogram import Client
from pyrogram.types import Message

# ---------------- Configuration ----------------
API_ID = int(os.environ.get("API_ID", "21302239"))
API_HASH = os.environ.get("API_HASH", "1560930c983fbca6a1fcc8eab760d40d")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7649467838:AAFe8VrdrSCeJeEBYhZCjRpNw36jLRISiEQ")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://<your-render-service>.onrender.com/")  # Render URL
PORT = int(os.environ.get("PORT", 5000))

# ---------------- Flask App ----------------
flask_app = Flask(__name__)

# ---------------- Pyrogram Bot ----------------
app = Client(
    "RenamerBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Temporary storage
user_files = {}
user_thumbs = {}

# ---------------- Bot Handlers ----------------
@app.on_message()
async def all_messages(client: Client, message: Message):
    user_id = message.from_user.id

    # /start
    if message.text and message.text.lower() == "/start":
        await message.reply_text(
            "👋 *Welcome!*\n\n"
            "📁 कोई भी file भेजो, मैं 1 sec में rename करके thumbnail लगाकर भेज दूँगा ✅\n\n"
            "🖼️ Thumbnail बदलना है? → कोई image भेज दो, वो thumbnail बन जाएगा 🚀"
        )
        return

    # Photo → thumbnail
    if message.photo:
        fd, thumb_path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)
        thumb_path = await message.download(file_name=thumb_path)
        old_thumb = user_thumbs.get(user_id)
        if old_thumb and os.path.exists(old_thumb):
            os.remove(old_thumb)
        user_thumbs[user_id] = thumb_path
        await message.reply_text("✅ Thumbnail saved! अब कोई video/file भेजो।")
        return

    # File → ask new name
    if message.document or message.video or message.audio:
        file = message.document or message.video or message.audio
        file_name = file.file_name
        await message.reply_text(
            f"📂 आपने भेजा है:\n`{file_name}`\n\n✏️ नया नाम भेजो (extension सही रखना, जैसे `.mp4`)"
        )
        user_files[user_id] = file.file_id
        return

    # Text → rename and send
    if message.text and user_id in user_files:
        file_id = user_files.pop(user_id)
        new_name = message.text.strip()
        try:
            path = await app.download_media(file_id)
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
