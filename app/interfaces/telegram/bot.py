from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters
)

from app.config import settings

from app.interfaces.telegram.handlers import (
    start_handler,
    message_handler
)


def create_bot():

    if not settings.telegram_bot_token:

        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not configured."
        )

    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start_handler
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler
        )
    )

    return application


def run_bot():

    application = create_bot()

    print("=" * 60)
    print("KiranaPilot Telegram Bot")
    print("Bot is running...")
    print("=" * 60)

    application.run_polling()