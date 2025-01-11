from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Bot handlers

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command handler."""
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
        "2️⃣ I’ll enhance it and provide a shareable link.\n\n"
        "🔗 <b>Explore:</b>\n"
        "  - <a href='https://t.me/TechPiroBots'>More Bots</a>\n\n"
        "👩‍💻 <b>Contact:</b> @Philowise"
    )
    await update.message.reply_text(
        text=help_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo uploads."""
    await update.message.reply_text(
        text="✨ <i>Processing your image...</i>", parse_mode=ParseMode.HTML
    )
    # Simulate processing steps
    await update.message.reply_text(
        text="✅ <b>All done!</b>\n🔗 <a href='https://example.com/your-image'>Here’s your image link.</a>",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=False,
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback handler for inline buttons."""
    query = update.callback_query
    await query.answer()

    if query.data == "help":
        await help_command(update, context)


# Main function
def main():
    """Main function to start the bot."""
    application = ApplicationBuilder().token("7252535128:AAHD-MNhGTVNXyI5l8a_Y12R4KkQ4DERPmA").build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Start the bot
    application.run_polling()


if __name__ == "__main__":
    main()
