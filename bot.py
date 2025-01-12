import os
import logging
import aiohttp
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, Dice
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
TOKEN = "7681342049:AAFatyO1DdQE4mmHrGYKcG3lnmIfDY-WQeg"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command handler."""
    first_name = update.effective_user.first_name or "User"

    # Reply keyboard for easy navigation
    reply_keyboard = [
        [KeyboardButton("/help"), KeyboardButton("/stats")],
    ]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

    # Welcome message
    welcome_message = (
        f"👋 <b>Welcome, {first_name}!</b>\n\n"
        f"📸 <i>Send me an image, and I’ll upload it for you!</i>\n\n"
        f"⚙️ Use the buttons below to navigate.\n\n"
        f"👩‍💻 Developed by: @Philowise\n"
        f"⚡️ <i>Let’s get started!</i>"
    )

    await update.message.reply_text(
        text=welcome_message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help command handler."""
    help_text = (
        "✨ <b>How to Use:</b>\n"
        "1️⃣ Send me an image.\n"
        "2️⃣ I’ll upload it and provide you with a shareable link.\n\n"
        "⚙️ <b>Commands:</b>\n"
        "• /start - Restart the bot.\n"
        "• /help - Show this help message.\n"
        "• /stats - View bot statistics.\n\n"
        "👩‍💻 <b>Contact:</b> @Philowise"
    )
    await update.message.reply_text(
        text=help_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stats command handler."""
    await update.message.reply_dice(emoji="🎯")
    stats_message = (
        f"📊 <b>Bot Statistics:</b>\n"
        f"👥 <b>Total Users:</b> Feature not implemented yet.\n"
        f"🖼️ <b>Total Images Processed:</b> Feature not implemented yet.\n\n"
        f"Thank you for using the bot!"
    )
    await update.message.reply_text(
        text=stats_message,
        parse_mode=ParseMode.HTML,
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process user-uploaded photos."""
    message = update.message

    # Step 1: Acknowledge the received image
    await message.reply_text("📸 <i>Image received! Uploading to Catbox...</i>", parse_mode=ParseMode.HTML)
    await message.reply_dice(emoji="🎲")

    # Step 2: Download the photo
    photo_file = await message.photo[-1].get_file()
    photo_path = f"{photo_file.file_id}.jpg"

    try:
        await photo_file.download_to_drive(photo_path)
        logging.info(f"Image downloaded to {photo_path}")

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
                        # Step 4: Send the URL to the user with an animation
                        await message.reply_dice(emoji="🎯")
                        await message.reply_text(
                            text=f"✅ <b>Upload successful!</b>\n🔗 <a href='{response_text.strip()}'>Here’s your link.</a>",
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=False,
                        )
                    else:
                        raise Exception(f"Unexpected response: {response_text}")

    except Exception as e:
        logging.error(f"Error processing photo: {e}")
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
