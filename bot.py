import os
import aiohttp
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

UPLOAD_API_URL = "https://catbox.moe/user/api.php"  # File hosting API endpoint
TOKEN = "7252535128:AAGWthnsH9cbYnjjmqkLmlraIGeBrIdzdTA"

# Database setup
DB_FILE = "bot_stats.db"


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
    """Update the user stats in the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Update user count if it's a new user
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
    """Retrieve the stats from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_count, image_count FROM stats WHERE id = 1")
    stats = cursor.fetchone()
    conn.close()
    return stats


# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command handler."""
    first_name = update.effective_user.first_name or "User"

    # Persistent reply keyboard
    reply_keyboard = [
        [KeyboardButton("/start"), KeyboardButton("/help"), KeyboardButton("/stats")],
    ]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

    welcome_message = (
        f"👋 <b>Welcome, {first_name}!</b>\n\n"
        f"📸 <i>Send me an image, and I’ll host it for you online!</i>\n\n"
        f"👩‍💻 Developed by: @Philowise\n"
        f"⚡️ <i>Let’s get started!</i>"
    )

    await update.message.reply_text(
        text=welcome_message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
    )


# Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help command handler."""
    help_text = (
        "✨ <b>How to Use:</b>\n"
        "1️⃣ Send me an image.\n"
        "2️⃣ I’ll upload it and provide you a shareable link.\n\n"
        "🔗 <b>Explore:</b>\n"
        "  - <a href='https://t.me/TechPiroBots'>More Bots</a>\n\n"
        "👩‍💻 <b>Contact:</b> @Philowise"
    )
    await update.message.reply_text(
        text=help_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )


# Stats command
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show statistics about users and images processed."""
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


# Photo handler
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Auto processes and uploads photos."""
    user_id = update.effective_user.id
    update_user_stats(user_id)  # Update stats for the user

    message = update.message
    await message.reply_text(
        text="✨ <i>Processing and uploading your image...</i>",
        parse_mode=ParseMode.HTML,
    )

    # Get the largest available image size
    photo_file = await message.photo[-1].get_file()
    photo_path = f"{photo_file.file_id}.jpg"

    try:
        # Download the photo
        await photo_file.download_to_drive(photo_path)

        # Upload the image to the hosting API
        async with aiohttp.ClientSession() as session:
            with open(photo_path, "rb") as file:
                data = aiohttp.FormData()
                data.add_field("reqtype", "fileupload")
                data.add_field("fileToUpload", file, filename=photo_path)

                async with session.post(UPLOAD_API_URL, data=data) as response:
                    if response.status == 200:
                        image_url = await response.text()
                        if image_url.startswith("https://"):
                            await message.reply_text(
                                text=f"✅ <b>Upload successful!</b>\n🔗 <a href='{image_url.strip()}'>Here’s your link.</a>",
                                parse_mode=ParseMode.HTML,
                                disable_web_page_preview=False,
                            )
                        else:
                            raise Exception("Unexpected response from the hosting service.")
                    else:
                        raise Exception("Failed to upload the file.")

    except Exception as e:
        await message.reply_text(
            text=f"❌ <b>Failed to process your image:</b> <i>{e}</i>",
            parse_mode=ParseMode.HTML,
        )

    finally:
        # Clean up the downloaded photo
        if os.path.exists(photo_path):
            os.remove(photo_path)


# Main function
def main():
    """Main function to start the bot."""
    initialize_db()  # Initialize the database
    application = ApplicationBuilder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Start the bot
    application.run_polling()


if __name__ == "__main__":
    main()
