import os
import base64
from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction
from .base import BaseModule

class MultimodalModule(BaseModule):
    """
    Handles photo and video uploads, downloads and encodes them to base64,
    and sends them to NVIDIA's multimodal Minimax-M3 model.
    """
    def register(self):
        # Listen for photo or video messages
        self.bot_app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, self.handle_multimodal))

    async def handle_multimodal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Downloads, encodes, and prompts the AI with uploaded media."""
        if not update.message:
            return

        chat = update.effective_chat
        message = update.message
        bot_username = context.bot.username

        # In groups/supergroups, only reply if mentioned or if replying to the bot's own message
        if chat.type in ["group", "supergroup"]:
            caption_text = message.caption or ""
            is_mentioned = f"@{bot_username}" in caption_text
            is_reply_to_bot = (
                message.reply_to_message and 
                message.reply_to_message.from_user and 
                message.reply_to_message.from_user.id == context.bot.id
            )
            if not (is_mentioned or is_reply_to_bot):
                return

        chat_id = chat.id
        session = self.session_manager.get_session(chat_id)
        
        # Determine media type and extract file info
        is_photo = bool(message.photo)
        is_video = bool(message.video)
        
        if not (is_photo or is_video):
            return

        # Notify the user that download is in progress
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)
        
        status_msg = await update.message.reply_text("📥 *Downloading and processing media...*", parse_mode="Markdown")

        try:
            if is_photo:
                # Grab the largest resolution image
                media = update.message.photo[-1]
                ext = "jpg"
                mime_type = "image/jpeg"
                media_type = "image_url"
                default_prompt = "Describe this image in detail."
            else:
                media = update.message.video
                ext = "mp4"
                mime_type = media.mime_type or "video/mp4"
                media_type = "video_url"
                default_prompt = "Describe this video in detail."

            # Setup temp directory inside workspace
            temp_dir = os.path.join(os.getcwd(), "temp_media")
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, f"{media.file_id}.{ext}")

            # Download the file via Telegram API
            telegram_file = await context.bot.get_file(media.file_id)
            await telegram_file.download_to_drive(custom_path=temp_path)

            # Read and encode to base64
            with open(temp_path, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode("utf-8")

            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

            # Extract caption or use default prompt
            prompt = message.caption or default_prompt
            prompt = prompt.replace(f"@{bot_username}", "").strip()
            if not prompt:
                prompt = default_prompt
            
            # Format the content dictionary as a list of parts for Minimax-M3
            media_part = {
                "type": media_type,
                media_type: {
                    "url": f"data:{mime_type};base64,{b64_data}"
                }
            }
            text_part = {
                "type": "text",
                "text": prompt
            }
            
            content_payload = [text_part, media_part]

            # In the user history, we store a human-readable snippet (e.g. "[Sent Image] Describe this image")
            # to prevent bloating history with base64 data, but we submit the full payload for the current turn.
            # We can temporarily add the payload to the api call, but store the reference text in history.
            # Let's save a placeholder in the session history so the history remains lightweight and doesn't crash on memory.
            history_prompt = f"[{'Photo' if is_photo else 'Video'}] {prompt}"
            
            # Build API messages: system + history + current payload
            api_messages = []
            if session.system_prompt:
                api_messages.append({"role": "system", "content": session.system_prompt})
            
            # Add past context
            api_messages.extend(session.history)
            
            # Add current multimodal turn
            api_messages.append({"role": "user", "content": content_payload})

            # Update the status message to indicate thinking
            await status_msg.edit_text("🧠 *AI is analyzing the media...*", parse_mode="Markdown")
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

            # Call NVIDIA API
            response_text = await self.nvidia_client.chat_completion(
                messages=api_messages,
                temperature=session.temperature,
                max_tokens=session.max_tokens,
                top_p=session.top_p
            )

            # Add lightweight representation of this interaction to session history
            session.add_message("user", history_prompt)
            session.add_message("assistant", response_text)

            # Delete the status message
            await status_msg.delete()

            # Reply to the user
            try:
                await update.message.reply_text(response_text, parse_mode="Markdown")
            except Exception:
                await update.message.reply_text(response_text)

        except Exception as e:
            await status_msg.edit_text(f"❌ *Failed to process media.* \nError: `{str(e)}`", parse_mode="Markdown")
