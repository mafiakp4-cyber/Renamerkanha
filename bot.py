import os
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import Message
from flask import Flask
import threading

# 🔑 Config (Environment Variables से)
API_ID = int(os.environ.get("API_ID", 21302239))
API_HASH = os.environ.get("API_HASH", "1560930c983fbca6a1fcc8eab760d40d")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8134357026:AAHxf3ncIOk9J4iNg2UHQ7cxeIlcQfnmLfU")

app = Client(
    "SongDownloaderBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Dummy Flask app for Render (port binding)
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "✅ Song Downloader Bot is running on Render!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port)

# 🎵 Song download command
@app.on_message(filters.command("song") & filters.private)
async def song_downloader(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("❌ Please provide a song name!\n\nExample: `/song Arijit Singh`")
        return

    query = " ".join(message.command[1:])
    await message.reply_text(f"🔎 Searching for **{query}** ...")

    try:
        # yt-dlp options
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": "%(title)s.%(ext)s",
            "noplaylist": True,
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)
            file_path = ydl.prepare_filename(info['entries'][0])
            title = info['entries'][0]['title']

        # Send mp3 to user
        await message.reply_audio(audio=file_path, title=title, caption=f"🎶 {title}")

        # delete file after sending
        os.remove(file_path)

    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("🚀 Song Downloader Bot started...")
    app.run()
