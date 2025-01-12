import os
import logging
import sqlite3
import aiohttp
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
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
TOKEN = "7252535128:AAGYfVDvl6QNVdIwXkKy7D0Uj6HxTr2teeY"

# Database file
DB_FILE = "bot_stats.db"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


def initialize_db():
    """Initialize the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_count INTEGER DEFAULT 0,
            image_count INTEGER DEFAULT 0
        )"""
    )
    cursor.execute("INSERT OR IGNORE INTO stats (id, user_count, image_count) VALUES (1, 0, 0)")
    conn.commit()
    conn.close()


def update_user_stats(user_id):
    """Update user and image stats in the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Increment user count if the user is new
    cursor.execute("SELECT user_count FROM stats WHERE id = 1")
    user_count = cursor.fetchone()[0]
    cursor.execute("SELECT DISTINCT user_id FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone() is None:
        user_count += 1
        cursor.execute("UPDATE stats SET user_count = ? WHERE id = 1", (user_count,))

    # Increment image count
    cursor.execute("SELECT image_count FROM stats WHERE id = 1")
    image_count = cursor.fetchone()[0] + 1
    cursor.execute("UPDATE stats SET image_count = ? WHERE id = 1", (image_count,))

    conn.commit()
    conn.close()


def get_stats():
    """Retrieve user and image stats from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_count, image_count FROM stats WHERE id = 1")
    stats = cursor.fetchone()
    conn.close()
    return stats


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command handler."""
    first_name = update.effective_user.first_name or "User"

    # Inline buttons for quick navigation
    inline_keyboard = [
        [InlineKeyboardButton("✨ Help", callback_data="help")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("🚀 Join Channel", url="https://t.me/TechPiroBots")],
    ]
    inline_markup = InlineKeyboardMarkup(inline_keyboard)

    # Reply keyboard for primary commands
    reply_keyboard = [
        [KeyboardButton("/help"), KeyboardButton("/stats")],
    ]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

    # Welcome message
    welcome_message = (
        f"👋 <b>Welcome, {first_name}!</b>\n\n"
        f"📸 <i>Send me an image, and I’ll process and host it for you!</i>\n\n"
        f"👩‍💻 Developed by: @Philowise\n"
        f"⚡️ <i>Let’s get started!</i>"
    )

    await update.message.reply_text(
        text=welcome_message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
    )

    await update.message.reply_text(
        text="🔽 Use the buttons below to explore features:",
        reply_markup=inline_markup,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help command handler."""
    help_text = (
        "✨ <b>How to Use:</b>\n"
        "1️⃣ Send me an image.\n"
        "2️⃣ I’ll process it and provide you with a shareable link.\n\n"
        "👩‍💻 <b>Contact:</b> @Philowise"
    )
    await update.message.reply_text(
        text=help_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stats command handler to display user and image stats."""
    user_count, image_count = get_stats()

    stats_message = (
        f"📊 <b>Bot Statistics:</b>\n"
        f"👥 <b>Total Users:</b> {user_count}\n"
        f"🖼️ <b>Total Images Processed:</b> {image_count}\n\n"
        f"Thank you for using the bot!"
    )

    await update.message.reply_text(
        text=stats_message,
        parse_mode=ParseMode.HTML,
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process and upload user-uploaded photos."""
    user_id = update.effective_user.id
    message = update.message

    # Update user stats
    update_user_stats(user_id)

    # Step 1: Acknowledge the received image
    await message.reply_text("📸 <i>Image received! Processing and uploading...</i>", parse_mode=ParseMode.HTML)

    # Step 2: Download and upload the photo
    photo_file = await message.photo[-1].get_file()
    photo_path = f"{photo_file.file_id}.jpg"

    try:
        # Download the photo
        await photo_file.download_to_drive(photo_path)
        logging.info(f"Image downloaded to {photo_path}")

        # Upload the photo to the hosting API
        async with aiohttp.ClientSession() as session:
            with open(photo_path, "rb") as file:
                data = aiohttp.FormData()
                data.add_field("reqtype", "fileupload")
                data.add_field("fileToUpload", file, filename=photo_path)

                async with session.post(UPLOAD_API_URL, data=data) as response:
                    response_text = await response.text()
                    logging.info(f"API Response: {response_text}")

                    if response.status == 200 and response_text.startswith("https://"):
                        # Send the URL to the user
                        await message.reply_text(
                            text=f"✅ <b>Upload successful!</b>\n🔗 <a href='{response_text.strip()}'>Here’s your link.</a>",
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=False,
                        )
                    else:
                        raise Exception(f"Unexpected response: {response_text}")

    except Exception as e:
        logging.error(f"Error uploading photo: {e}")
        await message.reply_text(
            text=f"❌ <b>Failed to process your image:</b> <i>{e}</i>",
            parse_mode=ParseMode.HTML,
        )

    finally:
        # Clean up the downloaded file
        if os.path.exists(photo_path):
            os.remove(photo_path)
            logging.info(f"Temporary file {photo_path} removed.")


def main():
    """Main entry point to run the bot."""
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
