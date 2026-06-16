from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction
from .base import BaseModule

class ChatModule(BaseModule):
    """
    Handles conversational text messages and clearing history.
    """
    def register(self):
        self.bot_app.add_handler(CommandHandler("clear", self.clear_command))
        self.bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))

    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Clears the conversational context for the current chat session."""
        if not update.message:
            return
            
        chat_id = update.effective_chat.id
        session = self.session_manager.get_session(chat_id)
        session.clear_history()
        await update.message.reply_text("🧹 *Conversation history has been cleared.*", parse_mode="Markdown")

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles user text messages, submits request to the model, and responds."""
        if not update.message or not update.message.text:
            return
            
        chat = update.effective_chat
        message = update.message
        bot_username = context.bot.username
        
        # In groups/supergroups, only reply if mentioned or if replying to the bot's own message
        if chat.type in ["group", "supergroup"]:
            is_mentioned = f"@{bot_username}" in message.text
            is_reply_to_bot = (
                message.reply_to_message and 
                message.reply_to_message.from_user and 
                message.reply_to_message.from_user.id == context.bot.id
            )
            if not (is_mentioned or is_reply_to_bot):
                return
            
        chat_id = chat.id
        user_message = message.text.replace(f"@{bot_username}", "").strip()
        
        # Retrieve or create session
        session = self.session_manager.get_session(chat_id)
        
        # Add user's message to chat history
        session.add_message("user", user_message)
        
        # Notify the user that the bot is thinking
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        
        # Get completion from NVIDIA
        messages = session.get_messages_for_api()
        response_text = await self.nvidia_client.chat_completion(
            messages=messages,
            temperature=session.temperature,
            max_tokens=session.max_tokens,
            top_p=session.top_p
        )
        
        # Add bot response to history
        session.add_message("assistant", response_text)
        
        # Send reply to Telegram
        try:
            await update.message.reply_text(response_text, parse_mode="Markdown")
        except Exception:
            # Fallback if markdown parsing fails due to malformed AI formatting
            await update.message.reply_text(response_text)
