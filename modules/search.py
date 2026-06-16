import asyncio
from duckduckgo_search import DDGS
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from telegram.constants import ChatAction
from .base import BaseModule

class SearchModule(BaseModule):
    """
    Provides internet search capability via DuckDuckGo and synthesizes findings using the Minimax-M3 model.
    """
    def register(self):
        self.bot_app.add_handler(CommandHandler("search", self.search_command))

    def _perform_search(self, query: str) -> str:
        """
        Synchronously performs search using DDG with the html backend.
        Returns a formatted string of the top results or an error message.
        """
        try:
            results = []
            with DDGS() as ddgs:
                # Use the html backend which has been verified to work reliably
                ddg_results = ddgs.text(query, backend="html")
                # Retrieve the top 5 results
                for r in list(ddg_results)[:5]:
                    results.append(
                        f"Title: {r.get('title')}\n"
                        f"URL: {r.get('href')}\n"
                        f"Snippet: {r.get('body')}\n"
                    )
            
            if not results:
                return "No search results found."
            return "\n---\n".join(results)
        except Exception as e:
            return f"Error executing search query: {e}"

    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Processes the /search command, calls DuckDuckGo, and summarizes results with Minimax-M3.
        """
        if not update.message:
            return
            
        chat_id = update.effective_chat.id
        args = context.args
        
        if not args:
            await update.message.reply_text(
                "🔍 *Internet Search Command*\n\n"
                "Usage:\n`/search <your search terms>`\n\n"
                "Example:\n`/search Nvidia Blackwell GPU release date`",
                parse_mode="Markdown"
            )
            return

        query = " ".join(args)
        
        # Trigger typing indicator
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        status_msg = await update.message.reply_text("🔍 *Searching the web...*", parse_mode="Markdown")

        try:
            # Execute search in a background thread to avoid blocking the event loop
            search_context = await asyncio.to_thread(self._perform_search, query)
            
            if "Error executing search query" in search_context or search_context == "No search results found.":
                await status_msg.edit_text(f"❌ *Failed to fetch search results.*\nDetail: `{search_context}`", parse_mode="Markdown")
                return

            # Update thinking status
            await status_msg.edit_text("🧠 *AI is synthesizing the search results...*", parse_mode="Markdown")
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

            # Retrieve chat settings session parameters
            session = self.session_manager.get_session(chat_id)

            # Set up RAG-specific instructions
            system_prompt = (
                "You are Omnibot, a helpful assistant with access to real-time DuckDuckGo search results.\n"
                "Your job is to answer the user's question accurately using ONLY the provided search results.\n\n"
                "Rules:\n"
                "- Synthesize the search results into a clean, detailed, and direct answer.\n"
                "- Cite your sources using standard Markdown links (e.g. [Title](URL)) inline or at the end of the message.\n"
                "- If the search results don't contain enough information to answer the question, state that clearly.\n"
                "- Decorate your response using relevant emojis to start sections/points.\n"
                "- Ensure formatting looks premium, well-structured, and clear in Telegram."
            )
            
            api_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"User Search Query: {query}\n\nSearch Results:\n{search_context}"}
            ]

            # Request completions from NVIDIA Minimax-M3
            response_text = await self.nvidia_client.chat_completion(
                messages=api_messages,
                temperature=0.3,  # Lower temperature for higher factual accuracy
                max_tokens=session.max_tokens,
                top_p=session.top_p
            )

            # Clean up progress message
            await status_msg.delete()

            # Respond to the user
            try:
                await update.message.reply_text(response_text, parse_mode="Markdown")
            except Exception:
                await update.message.reply_text(response_text)

            # Add this lookup to user session history representation
            session.add_message("user", f"[Web Search] {query}")
            session.add_message("assistant", response_text)

        except Exception as e:
            await status_msg.edit_text(f"❌ *Failed to synthesize search response.*\nError: `{str(e)}`", parse_mode="Markdown")
