import json
import re
import asyncio
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from telegram.constants import ChatAction
from .base import BaseModule

class QuizModule(BaseModule):
    """
    Generates interactive Telegram quiz polls dynamically on any topic chosen by the user.
    Uses Minimax-M3 to generate the quiz in structured JSON.
    """
    def register(self):
        self.bot_app.add_handler(CommandHandler("quiz", self.quiz_command))

    async def quiz_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /quiz <topic> command.
        """
        if not update.message:
            return
            
        chat_id = update.effective_chat.id
        args = context.args
        
        if not args:
            await update.message.reply_text(
                "🎮 *Interactive Quiz Mode*\n\n"
                "I can create native interactive Telegram quiz polls on any topic of your interest!\n\n"
                "Usage:\n`/quiz <your topic here>`\n\n"
                "Examples:\n"
                "• `/quiz space exploration`\n"
                "• `/quiz JavaScript coding`\n"
                "• `/quiz geography`\n"
                "• `/quiz video games`",
                parse_mode="Markdown"
            )
            return

        topic = " ".join(args)
        
        # Trigger typing indicator and send dice roll animation
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        dice_msg = await context.bot.send_dice(chat_id=chat_id, emoji="🎲")
        
        status_msg = await update.message.reply_text("🔮 *Quiz Master is reading your mind...*", parse_mode="Markdown")

        try:
            # NVIDIA prompt targeting JSON format with strict Telegram limits
            system_prompt = (
                "You are Omnibot, a quiz master. Create a multiple-choice quiz question based on the user's topic of interest.\n"
                "You MUST respond ONLY with a single raw JSON object matching the schema below. Do not output code block wrappers or extra text.\n\n"
                "JSON Schema:\n"
                "{\n"
                "  \"question\": \"The quiz question (must be under 280 characters)\",\n"
                "  \"options\": [\"Option 1\", \"Option 2\", \"Option 3\", \"Option 4\"], (exactly 4 options, each under 85 characters, DO NOT include color circles or number prefixes)\n"
                "  \"correct_option_index\": 1, (0-indexed integer matching the index of the correct answer, e.g. 0 to 3)\n"
                "  \"explanation\": \"Brief explanation of the correct answer (must be under 180 characters, start with a fun emoji)\"\n"
                "}\n\n"
                "Strict Constraints:\n"
                "- Keep the question concise and interesting.\n"
                "- All values must be well-formed JSON strings or integers.\n"
                "- Respect the character limits strictly, otherwise Telegram will reject the poll."
            )
            
            api_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a quiz on the topic: {topic}"}
            ]

            session = self.session_manager.get_session(chat_id)
            
            # Start query asynchronously
            ai_task = asyncio.create_task(
                self.nvidia_client.chat_completion(
                    messages=api_messages,
                    temperature=0.8,
                    max_tokens=1024,
                    top_p=0.9
                )
            )

            # Animate the loading status message in real time
            frames = [
                "🔮 *Quiz Master is reading your mind...*",
                "🌀 *Spinning up the quiz generators...*",
                "✨ *Weaving questions out of light...*",
                "⚡ *Electrifying the choices...*",
                "🔴 🎛️ *Calibrating options...*",
                "🔵 🧠 *Scanning neural pathways...*",
                "🟢 ⚡ *Generating answers...*",
                "🟡 🎯 *Finalizing layout...*"
            ]
            
            idx = 0
            while not ai_task.done():
                await asyncio.sleep(0.7)
                try:
                    await status_msg.edit_text(frames[idx % len(frames)], parse_mode="Markdown")
                except Exception:
                    pass
                idx += 1

            raw_response = await ai_task

            # Extract and parse JSON
            cleaned_json = raw_response.strip()
            # Remove markdown wrappers if the AI added them despite instructions
            if cleaned_json.startswith("```"):
                cleaned_json = re.sub(r"^```(?:json)?\n", "", cleaned_json)
                cleaned_json = re.sub(r"\n```$", "", cleaned_json)
            cleaned_json = cleaned_json.strip()

            try:
                quiz_data = json.loads(cleaned_json)
            except json.JSONDecodeError as jde:
                raise ValueError(f"Failed to decode quiz JSON. Response was: {cleaned_json}. Details: {jde}")

            # Verify schema compatibility
            question = quiz_data.get("question")
            options = quiz_data.get("options")
            correct_idx = quiz_data.get("correct_option_index")
            explanation = quiz_data.get("explanation")

            if not (question and options and isinstance(options, list) and len(options) >= 2):
                raise ValueError("Parsed JSON is missing required question or options fields.")

            if not isinstance(correct_idx, int) or correct_idx < 0 or correct_idx >= len(options):
                correct_idx = 0

            # Clean and truncate parameters to strictly fit Telegram API rules
            question = question[:290]
            
            # Format options with colorful bullet circle emojis programmatically
            colors = ["🔴", "🔵", "🟡", "🟢", "🟣", "🟠", "🟤", "⚫"]
            options_cleaned = []
            for i, opt in enumerate(options[:10]):
                emoji = colors[i % len(colors)]
                options_cleaned.append(f"{emoji} {opt[:85]}")

            explanation = explanation[:195] if explanation else None

            # Remove loading message
            await status_msg.delete()

            # Send the native Telegram quiz poll
            await context.bot.send_poll(
                chat_id=chat_id,
                question=question,
                options=options_cleaned,
                type="quiz",
                correct_option_id=correct_idx,
                explanation=explanation,
                explanation_parse_mode="Markdown" if explanation else None
            )

        except Exception as e:
            await status_msg.edit_text(
                f"❌ *Failed to generate quiz.*\n"
                f"Error: `{str(e)}`\n\n"
                "Please try again or try a different topic.", 
                parse_mode="Markdown"
            )
