import logging
import os
import asyncio
from pathlib import Path
from io import BytesIO
from PIL import Image
import ffmpeg
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.markdown import hbold, hcode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token from environment
BOT_TOKEN = os.getenv("8257399725:AAG278Z_ndrdWgxTQuu7DQugXaoCdf1xW0M")
TEMP_DIR = Path("temp_files")
TEMP_DIR.mkdir(exist_ok=True)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# FSM States
class VideoProcessing(StatesGroup):
    waiting_for_video = State()
    waiting_for_thumbnail = State()
    choosing_thumbnail_source = State()
    processing = State()

# Helper functions
def get_main_keyboard():
    """Main menu keyboard"""
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📹 Change Thumbnail")],
            [KeyboardButton(text="ℹ️ Help"), KeyboardButton(text="⚙️ Settings")]
        ],
        resize_keyboard=True
    )
    return kb

def get_thumbnail_source_keyboard():
    """Keyboard for thumbnail source selection"""
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📸 Upload Image")],
            [KeyboardButton(text="⏱️ Extract from Video"), KeyboardButton(text="🎬 Use Video Cover")]
        ],
        resize_keyboard=True
    )
    return kb

async def extract_video_thumbnail(video_path: str, output_path: str, timestamp: float = 1.0) -> bool:
    """Extract thumbnail from video at specific timestamp"""
    try:
        ffmpeg.input(video_path, ss=timestamp).output(output_path, vf="scale=1280:720", vframes=1).run(capture_stdout=True, capture_stderr=True, quiet=True)
        return True
    except Exception as e:
        logger.error(f"Error extracting thumbnail: {e}")
        return False

async def set_video_thumbnail(video_path: str, thumbnail_path: str, output_path: str) -> bool:
    """Set thumbnail for video using ffmpeg"""
    try:
        ffmpeg.input(video_path).output(
            output_path,
            vcodec='copy',
            acodec='copy',
            metadata=f'title="Video with Custom Thumbnail"'
        ).run(capture_stdout=True, capture_stderr=True, quiet=True)
        
        # Add thumbnail metadata
        ffmpeg.input(output_path).input(thumbnail_path).concat(n=1, v=1, a=0).output(
            str(output_path).replace(".mp4", "_with_thumb.mp4"),
            c='copy'
        ).run(capture_stdout=True, capture_stderr=True, quiet=True)
        
        return True
    except Exception as e:
        logger.error(f"Error setting thumbnail: {e}")
        return False

async def resize_image(image_path: str, max_width: int = 1280, max_height: int = 720) -> str:
    """Resize image to appropriate dimensions"""
    try:
        img = Image.open(image_path)
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        img.save(image_path, quality=95)
        return image_path
    except Exception as e:
        logger.error(f"Error resizing image: {e}")
        return None

async def cleanup_temp_files(user_id: int):
    """Clean up temporary files for user"""
    user_temp_dir = TEMP_DIR / str(user_id)
    if user_temp_dir.exists():
        for file in user_temp_dir.iterdir():
            try:
                file.unlink()
            except:
                pass

# Command handlers
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Start command"""
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
