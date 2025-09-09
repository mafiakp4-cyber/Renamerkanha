import os
from pyrogram import Client, filters
from pyrogram.types import Message

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

# ✅ Temporary memory storage
user_files = {}
user_thumbs = {}  # {user_id: thumb_path}

# Start Command
@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    await message.reply_text(
        "👋 *Welcome!*\n\n"
        "📁 कोई भी file भेजो, मैं 1 sec में rename करके thumbnail लगाकर भेज दूँगा ✅\n\n"
        "🖼️ Thumbnail बदलना है? → कोई image भेज दो, वो thumbnail बन जाएगा 🚀",
        quote=True
    )

# Step 1: जब user thumbnail भेजे
@app.on_message(filters.photo & filters.private)
async def save_thumb(client: Client, message: Message):
    user_id = message.from_user.id
    thumb_path = await message.download()
    user_thumbs[user_id] = thumb_path
    await message.reply_text("✅ Thumbnail saved! अब कोई video/file भेजो।", quote=True)

# Step 2: जब user file भेजे
@app.on_message((filters.document | filters.video | filters.audio) & filters.private)
async def ask_new_name(client: Client, message: Message):
    file = message.document or message.video or message.audio
    file_name = file.file_name

    await message.reply_text(
        f"📂 आपने भेजा है:\n`{file_name}`\n\n✏️ नया नाम भेजो (extension सही रखना, जैसे `.mp4`)",
        quote=True
    )

    user_files[message.from_user.id] = file.file_id

# Step 3: नया नाम लेकर rename + send
@app.on_message(filters.text & filters.private)
async def rename_file(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_files:
        return

    file_id = user_files.pop(user_id)
    new_name = message.text.strip()

    try:
        # Download file
        path = await client.download_media(file_id)
        new_path = os.path.join(os.getcwd(), new_name)
        os.rename(path, new_path)

        # Thumbnail check
        thumb = user_thumbs.get(user_id)

        # Upload back
        await message.reply_document(
            new_path,
            caption=f"✅ File renamed to `{new_name}`",
            thumb=thumb
        )
        os.remove(new_path)
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

print("🚀 Renamer Bot Started...")
app.run()
