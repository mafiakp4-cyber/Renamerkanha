import os
import openai
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from gtts import gTTS

# 🔑 API Keys
BOT_TOKEN = os.getenv("8547163783:AAHI80Wcdq54BWTCmdCAogISS_4kd6nMhYQ")  # Telegram Bot Token
OPENAI_API_KEY = os.getenv("AIzaSyAgACL6_KJX5Zt8xx5ncflKb3YXCLEin5Y")  # OpenAI Key
openai.api_key = OPENAI_API_KEY

# 🤖 ChatGPT Command
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = " ".join(context.args)
    if not user_input:
        await update.message.reply_text("💬 Usage: /chat your question")
        return

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": user_input}],
        )
        reply = response.choices[0].message.content
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# 🎨 AI Image Generator
async def image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("🖼️ Usage: /image describe the image you want")
        return

    try:
        response = openai.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="512x512"
        )
        image_url = response.data[0].url
        await update.message.reply_photo(photo=image_url, caption=f"🧠 Generated for: {prompt}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# 🧾 Text Summarizer
async def summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("📄 Usage: /summarize your text")
        return

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Summarize this: {text}"}],
        )
        summary = response.choices[0].message.content
        await update.message.reply_text(f"📝 Summary:\n\n{summary}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# 🎙️ Voice-to-Text (Whisper)
async def voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.voice:
        await update.message.reply_text("🎤 Please send a voice message.")
        return

    file = await update.message.voice.get_file()
    file_path = "voice.ogg"
    await file.download_to_drive(file_path)

    try:
        with open(file_path, "rb") as audio:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio
            )
        await update.message.reply_text(f"🗣️ Transcribed:\n\n{transcript.text}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    finally:
        os.remove(file_path)

# 🎧 Text-to-Speech
async def speak(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("🔊 Usage: /speak your text")
        return

    tts = gTTS(text=text, lang='en')
    audio_path = "output.mp3"
    tts.save(audio_path)

    await update.message.reply_audio(audio=InputFile(audio_path))
    os.remove(audio_path)

# 🚀 Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *AI Multi-Purpose Bot*\n\n"
        "Commands:\n"
        "💬 /chat — Chat with AI\n"
        "🖼️ /image — Generate Image\n"
        "🎙️ Send voice — Convert to text\n"
        "📄 /summarize — Summarize text\n"
        "🔊 /speak — Convert text to voice",
        parse_mode="Markdown"
    )

# Main
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("chat", chat))
    app.add_handler(CommandHandler("image", image))
    app.add_handler(CommandHandler("summarize", summarize))
    app.add_handler(CommandHandler("speak", speak))
    app.add_handler(MessageHandler(filters.VOICE, voice))

    print("🚀 Bot Started Successfully...")
    app.run_polling()
