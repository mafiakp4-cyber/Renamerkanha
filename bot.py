import os
import io
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaDocument

# ---------------- Config ----------------
API_ID = int(os.environ.get("API_ID", "21302239"))
API_HASH = os.environ.get("API_HASH", "1560930c983fbca6a1fcc8eab760d40d")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7649467838:AAFe8VrdrSCeJeEBYhZCjRpNw36jLRISiEQ")

# Increase workers for faster processing
app = Client(
    "RenamerBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=8
)

# ---------------- Memory Storage ----------------
user_files = {}     # {user_id: file_id}
user_thumbs = {}    # {user_id: bytesIO thumbnail}

# ---------------- Handlers ----------------
@app.on_message(filters.command("start") & filters.private)
async def start(client: Client, message: Message):
    await message.reply_text(
        "👋 *Welcome!*\n\n"
        "📁 कोई भी file भेजो, मैं 1 sec में rename करके thumbnail लगाकर भेज दूँगा ✅\n\n"
        "🖼️ Thumbnail बदलना है? → कोई image भेज दो, वो thumbnail बन जाएगा 🚀"
    )

# Save thumbnail in memory + resize
@app.on_message(filters.photo & filters.private)
async def save_thumb(client: Client, message: Message):
    user_id = message.from_user.id
    # Download photo in memory
    photo_bytes = await message.download(file_name=io.BytesIO())
    photo_bytes.seek(0)
    # Resize to 320x320
    img = Image.open(photo_bytes)
    img = img.convert("RGB")
    img.thumbnail((320, 320))
    thumb_bytes = io.BytesIO()
    img.save(thumb_bytes, format="JPEG")
    thumb_bytes.seek(0)
    user_thumbs[user_id] = thumb_bytes
    await message.reply_text("✅ Thumbnail saved! अब कोई video/file भेजो।")

# Receive file and ask for new name
@app.on_message((filters.document | filters.video | filters.audio) & filters.private)
async def ask_new_name(client: Client, message: Message):
    file = message.document or message.video or message.audio
    file_name = file.file_name
    user_files[message.from_user.id] = file.file_id
    await message.reply_text(
        f"📂 आपने भेजा है:\n`{file_name}`\n\n✏️ नया नाम भेजो (extension सही रखना, जैसे `.mp4`)"
    )

# Rename and send with thumbnail (memory-only)
@app.on_message(filters.text & filters.private)
async def rename_file(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_files:
        return

    file_id = user_files.pop(user_id)
    new_name = message.text.strip()
    try:
        # Download file in memory
        file_bytes = io.BytesIO()
        await client.download_media(file_id, file_bytes)
        file_bytes.seek(0)

        # Get thumbnail from memory
        thumb = user_thumbs.get(user_id)

        # Send file directly from memory
        await client.send_document(
            chat_id=message.chat.id,
            document=file_bytes,
            file_name=new_name,
            thumb=thumb,
            caption=f"✅ File renamed to `{new_name}`"
        )
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# ---------------- Main ----------------
print("🚀 Renamer Bot Started (1-sec thumbnail + rename)...")
app.run()
