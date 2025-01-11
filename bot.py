from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    first_name = update.effective_user.first_name or "User"

    # Inline keyboard with quick actions
    inline_keyboard = [
        [InlineKeyboardButton("✨ Help", callback_data="help")],
        [InlineKeyboardButton("🚀 Stats", callback_data="stats")],
        [InlineKeyboardButton("🔄 Restart", callback_data="restart")],
        [InlineKeyboardButton("📢 Join Channel", url="https://t.me/TechPiroBots")],
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard)

    # Welcome message
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


# Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Custom reply keyboard for main commands
    custom_keyboard = [
        [KeyboardButton("/start"), KeyboardButton("/stats")],
        [KeyboardButton("📸 Send an Image")],
    ]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)

    help_text = (
        "✨ <b>How to Use:</b>\n"
        "1️⃣ Send me an image.\n"
        "2️⃣ I’ll enhance it and provide a shareable link.\n\n"
        "🔗 <b>Explore:</b>\n"
        "  - <a href='https://t.me/TechPiroBots'>More Bots</a>\n\n"
        "👩‍💻 <b>Contact:</b> @Philowise"
    )

    await update.message.reply_text(
        text=help_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


# Stats command with inline buttons
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    stats_message = (
        "📊 <b>Bot Statistics:</b>\n"
        "👥 <b>Total Users:</b> 1523\n"
        "🖼️ <b>Total Images Processed:</b> 4567\n\n"
        "Keep using the bot to increase these numbers!"
    )

    keyboard = [
        [InlineKeyboardButton("🔄 Refresh Stats", callback_data="refresh_stats")],
        [InlineKeyboardButton("🏠 Home", callback_data="start")],
        [InlineKeyboardButton("🔄 Restart", callback_data="restart")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text=stats_message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


# Callback handler for inline buttons
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "help":
        await help_command(update, context)
    elif query.data == "stats":
        await stats_command(update, context)
    elif query.data == "restart":
        # Restart the bot's flow
        await start(update, context)
    elif query.data == "start":
        await start(update, context)


# Handler for photo uploads
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        text="✨ <i>Processing your image...</i>", parse_mode=ParseMode.HTML
    )

    # Simulate processing steps
    await update.message.reply_text(
        text="✅ <b>All done!</b>\n🔗 <a href='https://example.com/your-image'>Here’s your image link.</a>",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=False,
    )


# Main function
async def main() -> None:
    application = ApplicationBuilder().token("7252535128:AAHD-MNhGTVNXyI5l8a_Y12R4KkQ4DERPmA").build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Start polling
    await application.run_polling()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
