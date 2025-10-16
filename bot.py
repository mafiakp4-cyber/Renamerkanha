 import logging, os, asyncio, ffmpeg
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from pathlib import Path
from PIL import Image

logging.basicConfig(level=logging.INFO)
bot = Bot(token=os.getenv("8257399725:AAG278Z_ndrdWgxTQuu7DQugXaoCdf1xW0M"))
dp = Dispatcher()

TEMP_DIR = Path("temp_files")
TEMP_DIR.mkdir(exist_ok=True)

class ThumbChanger(StatesGroup):
    waiting_video = State()
    waiting_thumb = State()

def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🎬 Change Thumbnail")]],
        resize_keyboard=True
    )

@dp.message(Command("start"))
async def start_cmd(msg: types.Message):
    await msg.answer("👋 Welcome! Send a video to change its thumbnail.", reply_markup=main_keyboard())

@dp.message(F.text == "🎬 Change Thumbnail")
async def ask_video(msg: types.Message, state: FSMContext):
    await msg.answer("📹 Please send your video.", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ThumbChanger.waiting_video)

@dp.message(ThumbChanger.waiting_video, F.video)
async def receive_video(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    user_dir = TEMP_DIR / str(user_id)
    user_dir.mkdir(exist_ok=True)

    video_path = user_dir / "video.mp4"
    await bot.download(msg.video.file_id, video_path)

    await msg.answer("✅ Video received!\nNow send a thumbnail image (jpg/png).")
    await state.update_data(video_path=str(video_path))
    await state.set_state(ThumbChanger.waiting_thumb)

@dp.message(ThumbChanger.waiting_thumb, F.photo)
async def receive_thumb(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    video_path = data.get("video_path")
    user_id = msg.from_user.id
    thumb_path = TEMP_DIR / str(user_id) / "thumb.jpg"
    await bot.download(msg.photo[-1].file_id, thumb_path)

    # Resize image
    img = Image.open(thumb_path)
    img.thumbnail((1280, 720))
    img.save(thumb_path, quality=95)

    output_path = TEMP_DIR / str(user_id) / "final.mp4"

    # Fast thumbnail attach
    cmd = (
        ffmpeg
        .input(video_path)
        .output(output_path, **{
            "map": "0",
            "movflags": "+faststart",
            "attach": thumb_path,
            "metadata:s:t": "mimetype=image/jpeg"
        })
        .overwrite_output()
    )

    await msg.answer("⚙️ Processing...")
    cmd.run(quiet=True)

    await msg.answer_video(FSInputFile(output_path), caption="✅ Thumbnail updated successfully!")
    await state.clear()

@dp.message()
async def fallback(msg: types.Message):
    await msg.answer("❓ Use /start or press button to change video thumbnail.", reply_markup=main_keyboard())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())    """Start command"""
    await message.answer(
        f"👋 Welcome to Video Thumbnail Changer Bot!\n\n"
        f"I can help you change video thumbnails easily.\n\n"
        f"Use /help to see all available commands.",
        reply_markup=get_main_keyboard()
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Help command"""
    help_text = f"""
{hbold('📖 Available Commands:')}

/start - Start the bot
/help - Show this help message
/cancel - Cancel current operation
/settings - View settings

{hbold('🎯 How to use:')}

1. Click '{hbold('📹 Change Thumbnail')}' button
2. Send your video file
3. Choose thumbnail source:
   • Upload your own image
   • Extract frame from video
   • Use video's default cover
4. Process and download the result

{hbold('⚡ Features:')}
✅ Change video thumbnails
✅ Extract frames from videos
✅ Resize images automatically
✅ Support for MP4 videos
✅ Fast processing
✅ Privacy-friendly (files deleted after processing)
"""
    await message.answer(help_text, reply_markup=get_main_keyboard())

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Cancel operation"""
    await state.clear()
    await cleanup_temp_files(message.from_user.id)
    await message.answer("❌ Operation cancelled.", reply_markup=get_main_keyboard())

@dp.message(Command("settings"))
async def cmd_settings(message: types.Message):
    """Settings command"""
    settings_text = f"""
{hbold('⚙️ Settings')}

{hbold('Video Processing:')}
• Max thumbnail size: 1280x720px
• Supported formats: MP4
• Quality: High (95%)

{hbold('Privacy:')}
• All files are temporary
• Auto-delete after processing
• No data stored
"""
    await message.answer(settings_text, reply_markup=get_main_keyboard())

# Main workflow handlers
@dp.message(F.text == "📹 Change Thumbnail")
async def start_thumbnail_change(message: types.Message, state: FSMContext):
    """Start thumbnail change workflow"""
    user_temp_dir = TEMP_DIR / str(message.from_user.id)
    user_temp_dir.mkdir(exist_ok=True)
    
    await state.set_state(VideoProcessing.waiting_for_video)
    await message.answer(
        "📹 Please upload the video file you want to modify.\n\n"
        "Supported format: MP4",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(VideoProcessing.waiting_for_video, F.video)
async def receive_video(message: types.Message, state: FSMContext):
    """Receive video file"""
    try:
        user_id = message.from_user.id
        user_temp_dir = TEMP_DIR / str(user_id)
        
        status_msg = await message.answer("⏳ Downloading video...")
        
        video_file = await bot.get_file(message.video.file_id)
        video_path = user_temp_dir / f"input_video.mp4"
        
        await bot.download_file(video_file.file_path, video_path)
        
        await state.update_data(video_path=str(video_path))
        await state.set_state(VideoProcessing.choosing_thumbnail_source)
        
        await status_msg.delete()
        await message.answer(
            "✅ Video received!\n\n"
            "How would you like to set the thumbnail?",
            reply_markup=get_thumbnail_source_keyboard()
        )
    except Exception as e:
        logger.error(f"Error receiving video: {e}")
        await message.answer(f"❌ Error: {str(e)}")

@dp.message(VideoProcessing.choosing_thumbnail_source, F.text == "📸 Upload Image")
async def choose_upload_image(message: types.Message, state: FSMContext):
    """Choose to upload custom image"""
    await state.set_state(VideoProcessing.waiting_for_thumbnail)
    await message.answer(
        "📸 Please upload an image as thumbnail.\n\n"
        "Recommended size: 1280x720px",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(VideoProcessing.choosing_thumbnail_source, F.text == "⏱️ Extract from Video")
async def extract_thumbnail_handler(message: types.Message, state: FSMContext):
    """Extract thumbnail from video at specific timestamp"""
    await state.set_state(VideoProcessing.processing)
    data = await state.get_data()
    
    try:
        user_id = message.from_user.id
        user_temp_dir = TEMP_DIR / str(user_id)
        
        status_msg = await message.answer("⏳ Extracting thumbnail from video...")
        
        video_path = data.get("video_path")
        thumbnail_path = user_temp_dir / "extracted_thumbnail.png"
        
        success = await extract_video_thumbnail(video_path, str(thumbnail_path), timestamp=2.0)
        
        if success:
            await state.update_data(thumbnail_path=str(thumbnail_path))
            await process_video(message, state, status_msg)
        else:
            await status_msg.edit_text("❌ Failed to extract thumbnail")
    except Exception as e:
        logger.error(f"Error: {e}")
        await message.answer(f"❌ Error: {str(e)}")

@dp.message(VideoProcessing.waiting_for_thumbnail, F.photo)
async def receive_thumbnail_image(message: types.Message, state: FSMContext):
    """Receive thumbnail image"""
    try:
        user_id = message.from_user.id
        user_temp_dir = TEMP_DIR / str(user_id)
        
        status_msg = await message.answer("⏳ Processing thumbnail...")
        
        photo_file = await bot.get_file(message.photo[-1].file_id)
        thumbnail_path = user_temp_dir / "custom_thumbnail.png"
        
        await bot.download_file(photo_file.file_path, thumbnail_path)
        
        await resize_image(str(thumbnail_path))
        await state.update_data(thumbnail_path=str(thumbnail_path))
        await state.set_state(VideoProcessing.processing)
        
        await process_video(message, state, status_msg)
    except Exception as e:
        logger.error(f"Error receiving thumbnail: {e}")
        await message.answer(f"❌ Error: {str(e)}")

@dp.message(VideoProcessing.waiting_for_thumbnail, F.document)
async def receive_thumbnail_document(message: types.Message, state: FSMContext):
    """Receive thumbnail as document"""
    try:
        if message.document.mime_type not in ["image/png", "image/jpeg", "image/jpg"]:
            await message.answer("❌ Please upload an image file (PNG, JPG)")
            return
        
        user_id = message.from_user.id
        user_temp_dir = TEMP_DIR / str(user_id)
        
        status_msg = await message.answer("⏳ Processing thumbnail...")
        
        doc_file = await bot.get_file(message.document.file_id)
        ext = Path(message.document.file_name).suffix
        thumbnail_path = user_temp_dir / f"custom_thumbnail{ext}"
        
        await bot.download_file(doc_file.file_path, thumbnail_path)
        
        await resize_image(str(thumbnail_path))
        await state.update_data(thumbnail_path=str(thumbnail_path))
        await state.set_state(VideoProcessing.processing)
        
        await process_video(message, state, status_msg)
    except Exception as e:
        logger.error(f"Error receiving thumbnail: {e}")
        await message.answer(f"❌ Error: {str(e)}")

async def process_video(message: types.Message, state: FSMContext, status_msg: types.Message):
    """Process video with thumbnail"""
    try:
        data = await state.get_data()
        user_id = message.from_user.id
        user_temp_dir = TEMP_DIR / str(user_id)
        
        video_path = data.get("video_path")
        thumbnail_path = data.get("thumbnail_path")
        output_path = user_temp_dir / "output_video.mp4"
        
        await status_msg.edit_text("⏳ Applying thumbnail to video...")
        
        success = await set_video_thumbnail(video_path, thumbnail_path, str(output_path))
        
        if success and output_path.exists():
            await status_msg.edit_text("📤 Uploading video...")
            video_file = FSInputFile(str(output_path))
            await message.answer_video(
                video=video_file,
                caption="✅ Your video with new thumbnail is ready!",
                reply_markup=get_main_keyboard()
            )
        else:
            await status_msg.edit_text("❌ Failed to process video")
        
        await state.clear()
        await cleanup_temp_files(user_id)
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        await message.answer(f"❌ Error: {str(e)}")
        await state.clear()

# Error handler
@dp.message()
async def echo_handler(message: types.Message):
    """Fallback handler"""
    await message.answer(
        "I didn't understand that. Please use the buttons below or /help for commands.",
        reply_markup=get_main_keyboard()
    )

# Main function
async def main():
    """Start the bot"""
    logger.info("Bot starting...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
