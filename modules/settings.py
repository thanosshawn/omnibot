from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from .base import BaseModule

class SettingsModule(BaseModule):
    """
    Manages custom parameters for the current chat session.
    """
    def register(self):
        self.bot_app.add_handler(CommandHandler("system", self.system_command))
        self.bot_app.add_handler(CommandHandler("temperature", self.temperature_command))
        self.bot_app.add_handler(CommandHandler("info", self.info_command))

    async def system_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Allows users to view or update the system prompt context."""
        if not update.message:
            return
            
        chat_id = update.effective_chat.id
        session = self.session_manager.get_session(chat_id)
        
        args = context.args
        if not args:
            await update.message.reply_text(
                f"⚙️ *Current System Prompt*:\n`{session.system_prompt}`\n\n"
                "To update it, run:\n`/system <new instruction here>`",
                parse_mode="Markdown"
            )
            return
            
        new_prompt = " ".join(args)
        session.system_prompt = new_prompt
        await update.message.reply_text(
            f"✅ *System prompt updated context to*:\n`{new_prompt}`",
            parse_mode="Markdown"
        )

    async def temperature_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Allows users to view or update the generation temperature."""
        if not update.message:
            return
            
        chat_id = update.effective_chat.id
        session = self.session_manager.get_session(chat_id)
        
        args = context.args
        if not args:
            await update.message.reply_text(
                f"🌡️ *Current Temperature*: `{session.temperature}`\n\n"
                "To update it, run:\n`/temperature <float 0.0 - 1.0>`",
                parse_mode="Markdown"
            )
            return
            
        try:
            val = float(args[0])
            if not (0.0 <= val <= 1.0):
                raise ValueError()
            session.temperature = val
            await update.message.reply_text(f"✅ *Temperature updated to*: `{val}`", parse_mode="Markdown")
        except ValueError:
            await update.message.reply_text(
                "❌ *Invalid Value*: Please specify a float between 0.0 and 1.0 (e.g. `/temperature 0.7`).",
                parse_mode="Markdown"
            )

    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Displays settings state and metadata for the current chat session."""
        if not update.message:
            return
            
        chat_id = update.effective_chat.id
        session = self.session_manager.get_session(chat_id)
        history_len = len(session.history)
        
        info_text = (
            "ℹ️ *Current Session Status*\n\n"
            f"• *Chat ID*: `{chat_id}`\n"
            f"• *AI Model*: `minimaxai/minimax-m3` via NVIDIA\n"
            f"• *Temperature*: `{session.temperature}`\n"
            f"• *Max Tokens Limit*: `{session.max_tokens}`\n"
            f"• *Top P Value*: `{session.top_p}`\n"
            f"• *History Usage*: `{history_len}/20 messages` stored\n\n"
            f"• *System Instruction*:\n`{session.system_prompt}`"
        )
        await update.message.reply_text(info_text, parse_mode="Markdown")
