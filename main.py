import os
import sys
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes

import config
from nvidia_client import NvidiaClient
from session import SessionManager
from modules import load_modules

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Log the exception and notify the user (if update structure allows).
    """
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ An internal error occurred while processing your request. Please try again later."
            )
        except Exception as e:
            logger.error(f"Failed to send error message to user: {e}")

def main():
    # Verify environment configuration
    config_errors = config.check_config()
    if config_errors:
        for err in config_errors:
            logger.warning(err)
            
        # Hard stop if Telegram token is not available
        if not config.TELEGRAM_BOT_TOKEN:
            logger.critical("TELEGRAM_BOT_TOKEN is missing! Please configure it in your .env file.")
            sys.exit(1)

    logger.info("Starting Omnibot Initialization...")

    # Instantiate clients
    nvidia_client = NvidiaClient()
    session_manager = SessionManager()

    # Build python-telegram-bot Application
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Load all module plugins dynamically
    modules = load_modules(application, nvidia_client, session_manager)
    logger.info(f"Dynamic module loader registration complete. Loaded {len(modules)} module(s).")

    # Add error listener
    application.add_error_handler(error_handler)

    # Launch bot (Webhook for Render, Polling for local development)
    render_hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME")
    port_str = os.getenv("PORT")

    if render_hostname and port_str:
        port = int(port_str)
        # Construct the webhook URL using Render's automatically assigned hostname and the secret bot token
        webhook_url = f"https://{render_hostname}/{config.TELEGRAM_BOT_TOKEN}"
        
        logger.info("Detected Render hosting environment. Launching in Webhook mode...")
        logger.info(f"Configuring local server port: {port}")
        logger.info(f"Configuring webhook endpoint target: {webhook_url}")
        
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=config.TELEGRAM_BOT_TOKEN,
            webhook_url=webhook_url,
            allowed_updates=Update.ALL_TYPES
        )
    else:
        logger.info("Local environment detected. Starting bot via long polling...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
