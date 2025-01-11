# File: bot_polling.py

import os
import requests
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    Filters,
    CallbackContext,
)

FREE_UPSCALER_URL = "https://deepai.org/example-image-upscaling-api/image-upscale"
UPLOAD_API_URL = "https://catbox.moe/user/api.php"

# Global variables for stats
user_stats = set()
image_count = 0

# Start command
def start(update: Update, context: CallbackContext) -> None:
    global user_stats
    user_stats.add(update.effective_user.id)

    first_name = update.effective_user.first_name or "User"
    keyboard = [
        [InlineKeyboardButton("✨ Help", callback_data="help")],
        [InlineKeyboardButton("🚀 Join Our Channel", url="https://t.me/TechPiroBots")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_message = (
        f"👋 <b>Welcome, {first_name}!</b>\n\n"
        f"📸 <i>Send me an image, and I’ll upscale and host it for you!</i>\n"
        f"💡 <b>Features:</b>\n"
        f"  - High-quality image upscaling\n"
        f"  - Free hosting with instant links\n\n"
        f"👩‍💻 Developed by: @Philowise\n"
        f"⚡️ <i>Let’s get started!</i>"
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=welcome_message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
    )

# Help command
def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        "✨ <b>How to Use:</b>\n"
        "1️⃣ Send me an image.\n"
        "2️⃣ I’ll enhance it and provide a shareable link.\n\n"
        "🔗 <b>Explore:</b>\n"
        "  - <a href='https://t.me/TechPiroBots'>More Bots</a>\n\n"
        "👩‍💻 <b>Contact:</b> @Philowise"
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=help_text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )

# Stats command
def stats_command(update: Update, context: CallbackContext) -> None:
    global user_stats, image_count
    stats_message = (
        f"📊 <b>Bot Statistics:</b>\n"
        f"👥 <b>Total Users:</b> {len(user_stats)}\n"
        f"🖼️ <b>Total Images Processed:</b> {image_count}\n\n"
        f"Keep using the bot to increase these numbers!"
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=stats_message,
        parse_mode=ParseMode.HTML,
    )

# Callback handler for inline buttons
def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == "help":
        help_command(update, context)

# Handler for photos
def handle_photo(update: Update, context: CallbackContext) -> None:
    global user_stats, image_count
    user_stats.add(update.effective_user.id)
    image_count += 1

    if not update.message.photo:
        context.bot.send_message(chat_id=update.effective_chat.id, text="🚫 Please send a valid image.")
        return

    photo_file = update.message.photo[-1].get_file()
    photo_path = f"temp/{photo_file.file_id}.jpg"
    upscaled_path = f"temp/upscaled_{photo_file.file_id}.jpg"

    os.makedirs("temp", exist_ok=True)
    photo_file.download(photo_path)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="✨ <i>Processing your image...</i>",
        parse_mode=ParseMode.HTML,
    )

    try:
        # Step 1: Upscale the image
        with open(photo_path, "rb") as image_file:
            response = requests.post(FREE_UPSCALER_URL, files={"image": image_file})

        if response.status_code == 200 and "upscaled_image" in response.json():
            upscaled_image_url = response.json()["upscaled_image"]
            with open(upscaled_path, "wb") as f:
                f.write(requests.get(upscaled_image_url).content)
        else:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ <i>Upscaling failed. Uploading the original image.</i>",
                parse_mode=ParseMode.HTML,
            )
            upscaled_path = photo_path

        # Step 2: Upload the processed image
        with open(upscaled_path, "rb") as image_file:
            upload_response = requests.post(
                UPLOAD_API_URL,
                data={"reqtype": "fileupload"},
                files={"fileToUpload": image_file},
            )

        if upload_response.status_code == 200 and upload_response.text.startswith("https://"):
            image_url = upload_response.text.strip()
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"✅ <b>All done!</b>\n🔗 <a href='{image_url}'>Here’s your image link.</a>",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=False,
            )
        else:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ <b>Failed to upload the image. Please try again later.</b>",
                parse_mode=ParseMode.HTML,
            )
    except Exception as e:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ <b>An error occurred:</b> <i>{str(e)}</i>",
            parse_mode=ParseMode.HTML,
        )
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)
        if os.path.exists(upscaled_path) and upscaled_path != photo_path:
            os.remove(upscaled_path)

# Main function
def main() -> None:
    TELEGRAM_BOT_TOKEN = "7252535128:AAH7JUQw0uyr4TDRMaKxmhnXf8ubzo6ZCcw"
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("stats", stats_command))
    dispatcher.add_handler(MessageHandler(Filters.photo, handle_photo))
    dispatcher.add_handler(CallbackQueryHandler(button_callback))

    # Start polling
    updater.start_polling()
    print("Bot is running...")
    updater.idle()

if __name__ == "__main__":
    main()
