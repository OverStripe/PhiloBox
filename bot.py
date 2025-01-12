import os
import logging
import sqlite3
import aiohttp
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InputFile
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Hosting API URL
UPLOAD_API_URL = "https://catbox.moe/user/api.php"

# Telegram Bot Token
TOKEN = "7681342049:AAEnZgHp16kMhd40Nmiw1k1w0Lc6hdBmD0o"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Database setup
DB_FILE = "bot_stats.db"


def initialize_db():
    """Initialize the database for storing user stats and images processed."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            images_processed INTEGER DEFAULT 0
        )
        """
    )
    conn.commit()
    conn.close()


def update_user_stats(user_id):
    """Update the stats for a user in the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO stats (user_id, images_processed) VALUES (?, 0)", (user_id,)
    )
    cursor.execute(
        "UPDATE stats SET images_processed = images_processed + 1 WHERE user_id = ?",
        (user_id,),
    )
    conn.commit()
    conn.close()


def get_total_stats():
    """Get total users and images processed from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(user_id), SUM(images_processed) FROM stats")
    stats = cursor.fetchone()
    conn.close()
    total_users = stats[0] if stats[0] else 0
    total_images = stats[1] if stats[1] else 0
    return total_users, total_images


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command handler."""
    first_name = update.effective_user.first_name or "User"

    # Reply keyboard for easy navigation
    reply_keyboard = [
        [KeyboardButton("/help"), KeyboardButton("/stats")],
    ]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

    # Welcome text
    welcome_message = (
        f"👋 Welcome, {first_name}!\n\n"
        f"📸 Send me an image, and I’ll upload it for you!\n\n"
        f"🚀 Use the buttons below to navigate.\n\n"
        f"👩‍💻 Developed by: @Philowise"
    )

    # Send image and welcome text
    image_url = "https://files.catbox.moe/zscaaa.jpg"
    await update.message.reply_photo(photo=image_url, caption=welcome_message, reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help command handler."""
    help_text = (
        "✨ How to Use:\n"
        "1️⃣ Send me an image.\n"
        "2️⃣ I’ll upload it and provide you with a shareable link.\n\n"
        "⚙️ Commands:\n"
        "/start - Restart the bot\n"
        "/help - Show this help message\n"
        "/stats - View bot statistics\n\n"
        "👩‍💻 Contact: @Philowise"
    )
    await update.message.reply_text(
        text=help_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stats command handler."""
    total_users, total_images = get_total_stats()
    stats_message = (
        f"📊 Bot Statistics:\n"
        f"👥 Total Users: {total_users}\n"
        f"🖼️ Total Images Processed: {total_images}\n\n"
        f"Thank you for using the bot!"
    )
    await update.message.reply_text(
        text=stats_message,
        parse_mode=ParseMode.HTML,
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process user-uploaded photos."""
    user_id = update.effective_user.id
    message = update.message

    # Step 1: Acknowledge the received image
    await message.reply_text("📸 Image received! Uploading to Catbox...")

    # Step 2: Download the photo
    photo_file = await message.photo[-1].get_file()
    photo_path = f"{photo_file.file_id}.jpg"

    try:
        await photo_file.download_to_drive(photo_path)
        logging.info(f"Image downloaded to {photo_path}")

        # Update user stats
        update_user_stats(user_id)

        # Step 3: Upload the photo to Catbox
        async with aiohttp.ClientSession() as session:
            with open(photo_path, "rb") as file:
                data = aiohttp.FormData()
                data.add_field("reqtype", "fileupload")
                data.add_field("fileToUpload", file, filename=photo_path)

                async with session.post(UPLOAD_API_URL, data=data) as response:
                    response_text = await response.text()
                    logging.info(f"API Response: {response_text}")

                    if response.status == 200 and response_text.startswith("https://"):
                        # Step 4: Send the URL to the user
                        await message.reply_text(
                            text=f"✅ Upload successful!\n🔗 <a href='{response_text.strip()}'>Here’s your link.</a>",
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=False,
                        )
                    else:
                        raise Exception(f"Unexpected response: {response_text}")

    except Exception as e:
        logging.error(f"Error processing photo: {e}")
        await message.reply_text(
            text=f"❌ Failed to process your image: {e}",
            parse_mode=ParseMode.HTML,
        )

    finally:
        # Clean up the downloaded file
        if os.path.exists(photo_path):
            os.remove(photo_path)
            logging.info(f"Temporary file {photo_path} removed.")


def main():
    """Main entry point to run the bot."""
    # Initialize database
    initialize_db()

    application = ApplicationBuilder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Start polling
    application.run_polling()


if __name__ == "__main__":
    main()
