import asyncio
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from telegram.constants import ChatAction
from .base import BaseModule

class GroupModule(BaseModule):
    """
    Plugin module providing group conversation intelligence.
    Allows the bot to summarize group discussion, identify topics,
    analyze sentiment, adapt its system persona, and toggle auto-reply mode.
    """
    def register(self):
        self.bot_app.add_handler(CommandHandler("summary", self.summary_command))
        self.bot_app.add_handler(CommandHandler("topics", self.topics_command))
        self.bot_app.add_handler(CommandHandler("sentiment", self.sentiment_command))
        self.bot_app.add_handler(CommandHandler("adapt", self.adapt_command))
        self.bot_app.add_handler(CommandHandler("toggle_auto", self.toggle_auto_command))

    async def summary_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generates an executive summary of the rolling group memory transcript."""
        if not update.message:
            return
            
        chat_id = update.effective_chat.id
        session = self.session_manager.get_session(chat_id)
        
        if not session.group_memory:
            await update.message.reply_text(
                "📝 *No conversation context yet.* Chat in this group first to build memory!",
                parse_mode="Markdown"
            )
            return
            
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        status_msg = await update.message.reply_text("📝 *Synthesizing group discussion summary...*", parse_mode="Markdown")
        
        try:
            transcript = session.get_group_transcript()
            system_prompt = (
                "You are Omnibot, a helpful group assistant. Synthesize the provided group chat transcript "
                "into a concise, highly structured executive summary. Highlight the key questions asked, "
                "decisions made, and overall topics discussed. Decorate your summary with relevant emojis "
                "and format clearly in Markdown with clean headers."
            )
            
            api_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Group Chat Transcript:\n{transcript}"}
            ]
            
            summary = await self.nvidia_client.chat_completion(
                messages=api_messages,
                temperature=0.5,
                max_tokens=2048,
                top_p=0.9
            )
            
            await status_msg.delete()
            await update.message.reply_text(summary, parse_mode="Markdown")
            
        except Exception as e:
            await status_msg.edit_text(f"❌ *Failed to generate summary.* \nError: `{str(e)}`", parse_mode="Markdown")

    async def topics_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Extracts and lists the active topics of discussion in the group memory."""
        if not update.message:
            return
            
        chat_id = update.effective_chat.id
        session = self.session_manager.get_session(chat_id)
        
        if not session.group_memory:
            await update.message.reply_text(
                "🏷️ *No conversation context yet.* Chat in this group first to build memory!",
                parse_mode="Markdown"
            )
            return
            
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        status_msg = await update.message.reply_text("🏷️ *Extracting main topics of interest...*", parse_mode="Markdown")
        
        try:
            transcript = session.get_group_transcript()
            system_prompt = (
                "You are Omnibot, a helpful assistant. Analyze the provided group chat transcript "
                "and extract a list of the main topics discussed. Present them as a bulleted list "
                "with a brief, structured description/summary for each topic. Use relevant emojis."
            )
            
            api_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Group Chat Transcript:\n{transcript}"}
            ]
            
            topics = await self.nvidia_client.chat_completion(
                messages=api_messages,
                temperature=0.4,
                max_tokens=2048,
                top_p=0.9
            )
            
            await status_msg.delete()
            await update.message.reply_text(topics, parse_mode="Markdown")
            
        except Exception as e:
            await status_msg.edit_text(f"❌ *Failed to extract topics.* \nError: `{str(e)}`", parse_mode="Markdown")

    async def sentiment_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Analyzes the overall sentiment and emotional tone of the group."""
        if not update.message:
            return
            
        chat_id = update.effective_chat.id
        session = self.session_manager.get_session(chat_id)
        
        if not session.group_memory:
            await update.message.reply_text(
                "🎭 *No conversation context yet.* Chat in this group first to build memory!",
                parse_mode="Markdown"
            )
            return
            
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        status_msg = await update.message.reply_text("🎭 *Analyzing the group's mood and sentiment...*", parse_mode="Markdown")
        
        try:
            transcript = session.get_group_transcript()
            system_prompt = (
                "You are Omnibot, a helpful assistant. Analyze the provided group chat transcript "
                "and assess the overall group sentiment (e.g., positive, technical/coding-focused, frustrated, friendly). "
                "Provide a brief explanation of the emotional dynamics observed. Decorate with relevant emojis."
            )
            
            api_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Group Chat Transcript:\n{transcript}"}
            ]
            
            sentiment = await self.nvidia_client.chat_completion(
                messages=api_messages,
                temperature=0.5,
                max_tokens=1024,
                top_p=0.9
            )
            
            await status_msg.delete()
            await update.message.reply_text(sentiment, parse_mode="Markdown")
            
        except Exception as e:
            await status_msg.edit_text(f"❌ *Failed to analyze sentiment.* \nError: `{str(e)}`", parse_mode="Markdown")

    async def adapt_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Analyzes the group tone and dynamically updates the bot's system persona to match."""
        if not update.message:
            return
            
        chat_id = update.effective_chat.id
        session = self.session_manager.get_session(chat_id)
        
        if not session.group_memory:
            await update.message.reply_text(
                "🌀 *No conversation context yet.* Chat in this group first so I can learn your tone!",
                parse_mode="Markdown"
            )
            return
            
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        status_msg = await update.message.reply_text("🌀 *Analyzing conversation flow to adapt my persona...*", parse_mode="Markdown")
        
        try:
            transcript = session.get_group_transcript()
            system_prompt = (
                "You are Omnibot, a highly adaptive AI assistant. You are reviewing the group transcript to adjust "
                "your personality and prompt guidelines so you can integrate seamlessly. Analyze the group's tone, "
                "topics of interest, and vocabulary. Based on this, generate a NEW system prompt for yourself.\n\n"
                "Constraints:\n"
                "1. Maintain your core identity as Omnibot (helpful, friendly, multimodal AI).\n"
                "2. Adapt your tone (e.g. casual, professional, tech-focused, sarcastic, friendly) to match the group's style.\n"
                "3. Keep the prompt under 350 characters.\n"
                "4. Respond ONLY with the raw text of the new system prompt. Do not output markdown code blocks or wrapper text."
            )
            
            api_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Group Chat Transcript:\n{transcript}"}
            ]
            
            new_prompt = await self.nvidia_client.chat_completion(
                messages=api_messages,
                temperature=0.8,
                max_tokens=512,
                top_p=0.9
            )
            
            cleaned_prompt = new_prompt.strip()
            # Clean up potential markdown wrappers
            if cleaned_prompt.startswith("```"):
                import re
                cleaned_prompt = re.sub(r"^```(?:text|plain)?\n", "", cleaned_prompt)
                cleaned_prompt = re.sub(r"\n```$", "", cleaned_prompt)
            cleaned_prompt = cleaned_prompt.strip()
            
            # Apply adaptation
            session.system_prompt = cleaned_prompt
            
            await status_msg.delete()
            await update.message.reply_text(
                f"🔄 *Omnibot has adapted to the group's tone!*\n\n"
                f"*Updated System Persona*:\n`{cleaned_prompt}`",
                parse_mode="Markdown"
            )
            
        except Exception as e:
            await status_msg.edit_text(f"❌ *Failed to adapt persona.* \nError: `{str(e)}`", parse_mode="Markdown")

    async def toggle_auto_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggles whether the bot responds to all messages or only direct mentions."""
        if not update.message:
            return
            
        chat_id = update.effective_chat.id
        session = self.session_manager.get_session(chat_id)
        
        session.auto_reply = not session.auto_reply
        
        status_text = "ON 🟢" if session.auto_reply else "OFF 🔴"
        action_text = (
            "I will now chime in on all text messages in this group."
            if session.auto_reply else
            "I will only respond when directly mentioned (using @username) or replied to."
        )
        
        await update.message.reply_text(
            f"🤖 *Auto-Reply Mode is now {status_text}*\n\n"
            f"_{action_text}_",
            parse_mode="Markdown"
        )
