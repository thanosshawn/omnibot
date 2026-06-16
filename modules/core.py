from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from .base import BaseModule

class CoreModule(BaseModule):
    """
    Handles core bot navigation and helper commands (/start, /help).
    """
    def register(self):
        self.bot_app.add_handler(CommandHandler("start", self.start_command))
        self.bot_app.add_handler(CommandHandler("help", self.help_command))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Responds to /start, clears session history, and displays a welcome message.
        """
        if not update.message:
            return
            
        chat_id = update.effective_chat.id
        session = self.session_manager.get_session(chat_id)
        session.clear_history()  # Reset conversation on start
        
        welcome_text = (
            "👋 *Hello! I am Omnibot.*\n\n"
            "I am a modular Telegram bot powered by NVIDIA's *Minimax-M3* multimodal AI model.\n\n"
            "Here is what I can do:\n"
            "💬 *Text Chat*: Simply send me a text message. I remember recent conversation context!\n"
            "📸 *Analyze Images*: Send a photo (with or without a caption) to ask questions about it.\n"
            "🎥 *Analyze Videos*: Send a short video to query its content.\n\n"
            "Use /help to see all available command configurations."
        )
        await update.message.reply_text(welcome_text, parse_mode="Markdown")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Responds to /help, describing user commands and features.
        """
        if not update.message:
            return
            
        help_text = (
            "🤖 *Omnibot Helper Menu*\n\n"
            "*Commands*:\n"
            "• `/start` - Displays the welcome message and resets chat history.\n"
            "• `/help` - Displays this help message.\n"
            "• `/clear` - Wipes active conversation memory.\n"
            "• `/system <text>` - Configures a custom system prompt instruction (e.g. `/system Speak like a pirate`).\n"
            "• `/temperature <0.0-1.0>` - Configures generation temperature (e.g. `/temperature 0.7`).\n"
            "• `/info` - Inspects current session settings and history status.\n\n"
            "*Usage Tips*:\n"
            "• Send standard text messages to chat normally.\n"
            "• Send an image or video with an optional text caption to query visual media."
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")
