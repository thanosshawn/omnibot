import asyncio
import requests
import subprocess
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from telegram.constants import ChatAction
from .base import BaseModule
import config

class InternetModule(BaseModule):
    """
    Plugin module providing internet access capabilities.
    Leverages zero-config endpoints (like Jina Reader) to fetch and search web content,
    bringing the context back into the group discussion.
    """
    def register(self):
        self.bot_app.add_handler(CommandHandler("read", self.read_command))
        self.bot_app.add_handler(CommandHandler("search", self.search_command))
        self.bot_app.add_handler(CommandHandler("twitter", self.twitter_command))
        self.bot_app.add_handler(CommandHandler("reddit", self.reddit_command))
        self.bot_app.add_handler(CommandHandler("setcookie", self.setcookie_command))
        
        # Configure agent-reach if cookies are present in environment
        if getattr(config, "TWITTER_COOKIE", None):
            try:
                subprocess.run(["agent-reach", "configure", "twitter-cookies", config.TWITTER_COOKIE], check=True, capture_output=True)
            except Exception as e:
                print(f"[InternetModule] Failed to auto-configure Twitter cookie: {e}")

    async def read_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reads a webpage and provides a summary or context for the AI."""
        if not update.message or not context.args:
            await update.message.reply_text(
                "❌ *Usage*: `/read <URL>`\nExample: `/read https://github.com/Panniantong/agent-reach`",
                parse_mode="Markdown"
            )
            return

        url = context.args[0]
        chat_id = update.effective_chat.id
        
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        status_msg = await update.message.reply_text("🌐 *Reading webpage...*", parse_mode="Markdown")
        
        try:
            # We use Jina Reader as configured by agent-reach zero-config principles
            response = await asyncio.to_thread(requests.get, f"https://r.jina.ai/{url}", timeout=20)
            response.raise_for_status()
            
            content = response.text
            # Truncate content to avoid exceeding token limits
            if len(content) > 10000:
                content = content[:10000] + "\n...[truncated]..."

            # Summarize the content using the LLM
            system_prompt = (
                "You are Omnibot, a highly capable assistant. You have just scraped the contents of a webpage. "
                "Provide a concise, highly readable summary of the webpage. Highlight the main points, key features, "
                "or important details. Decorate with emojis and structure with markdown."
            )
            
            api_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"URL: {url}\n\nWebpage Content:\n{content}"}
            ]
            
            summary = await self.nvidia_client.chat_completion(
                messages=api_messages,
                temperature=0.4,
                max_tokens=2048,
                top_p=0.9
            )
            
            await status_msg.delete()
            await update.message.reply_text(summary, parse_mode="Markdown", disable_web_page_preview=True)
            
        except Exception as e:
            await status_msg.edit_text(f"❌ *Failed to read webpage.* \nError: `{str(e)}`", parse_mode="Markdown")

    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Searches the internet and synthesizes an answer."""
        if not update.message or not context.args:
            await update.message.reply_text(
                "❌ *Usage*: `/search <query>`\nExample: `/search latest AI news`",
                parse_mode="Markdown"
            )
            return

        query = " ".join(context.args)
        chat_id = update.effective_chat.id
        
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        status_msg = await update.message.reply_text(f"🔍 *Searching the web for:* `{query}`...", parse_mode="Markdown")
        
        try:
            # Using Jina Search for semantic web search results
            response = await asyncio.to_thread(
                requests.get, 
                f"https://s.jina.ai/{query}", 
                headers={"Accept": "application/json"},
                timeout=20
            )
            response.raise_for_status()
            
            data = response.json()
            search_results = data.get("data", [])
            
            if not search_results:
                await status_msg.edit_text("❌ No relevant search results found.")
                return
                
            # Compile search context
            context_text = ""
            for item in search_results[:5]: # Take top 5 results
                context_text += f"Title: {item.get('title', 'No Title')}\n"
                context_text += f"URL: {item.get('url', 'No URL')}\n"
                context_text += f"Description: {item.get('description', 'No Description')}\n\n"
                
            system_prompt = (
                "You are Omnibot, a highly capable assistant. You have just performed a web search. "
                "Synthesize an answer to the user's query based strictly on the provided search results. "
                "Cite your sources using the provided URLs. Be concise, highly readable, and use markdown."
            )
            
            api_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Search Query: {query}\n\nSearch Results:\n{context_text}"}
            ]
            
            answer = await self.nvidia_client.chat_completion(
                messages=api_messages,
                temperature=0.3,
                max_tokens=2048,
                top_p=0.9
            )
            
            await status_msg.delete()
            await update.message.reply_text(answer, parse_mode="Markdown", disable_web_page_preview=True)
            
        except Exception as e:
            await status_msg.edit_text(f"❌ *Failed to search the web.* \nError: `{str(e)}`", parse_mode="Markdown")

    async def twitter_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Searches Twitter using the twitter-cli."""
        if not update.message or not context.args:
            await update.message.reply_text("❌ *Usage*: `/twitter <query>`", parse_mode="Markdown")
            return
        query = " ".join(context.args)
        chat_id = update.effective_chat.id
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        status_msg = await update.message.reply_text(f"🐦 *Searching Twitter for:* `{query}`...", parse_mode="Markdown")
        try:
            proc = await asyncio.to_thread(
                subprocess.run, 
                ["twitter", "search", query, "--limit", "10"], 
                capture_output=True, 
                text=True, 
                encoding="utf-8"
            )
            if proc.returncode != 0:
                err_msg = proc.stderr or proc.stdout
                if "login" in err_msg.lower() or "cookie" in err_msg.lower():
                    await status_msg.edit_text("❌ *Twitter search failed.* Authentication cookie is missing or invalid. Use `/setcookie twitter <cookie>`.")
                    return
                raise Exception(f"twitter-cli failed: {err_msg}")
            
            output = proc.stdout
            if not output or len(output.strip()) == 0:
                 await status_msg.edit_text("❌ No relevant tweets found.")
                 return
                 
            if len(output) > 8000:
                output = output[:8000] + "\n...[truncated]..."
                
            system_prompt = (
                "You are Omnibot. You just searched Twitter. Synthesize an answer or summary based strictly on these tweets. "
                "Quote interesting tweets if relevant. Be concise, engaging, and use markdown."
            )
            api_messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Query: {query}\n\nResults:\n{output}"}]
            answer = await self.nvidia_client.chat_completion(messages=api_messages, temperature=0.4, max_tokens=2048, top_p=0.9)
            await status_msg.delete()
            await update.message.reply_text(answer, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception as e:
            await status_msg.edit_text(f"❌ *Failed to search Twitter.* \nError: `{str(e)}`", parse_mode="Markdown")

    async def reddit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Searches Reddit using the public JSON API."""
        if not update.message or not context.args:
            await update.message.reply_text("❌ *Usage*: `/reddit <query>`", parse_mode="Markdown")
            return
        query = " ".join(context.args)
        chat_id = update.effective_chat.id
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        status_msg = await update.message.reply_text(f"👾 *Searching Reddit for:* `{query}`...", parse_mode="Markdown")
        try:
            headers = {"User-Agent": "Omnibot/1.0"}
            response = await asyncio.to_thread(
                requests.get, 
                f"https://www.reddit.com/search.json?q={query}&limit=5", 
                headers=headers,
                timeout=20
            )
            response.raise_for_status()
            data = response.json()
            posts = data.get("data", {}).get("children", [])
            
            if not posts:
                await status_msg.edit_text("❌ No relevant Reddit posts found.")
                return
                
            context_text = ""
            for post in posts:
                p = post.get("data", {})
                context_text += f"Title: {p.get('title', '')}\n"
                context_text += f"Subreddit: {p.get('subreddit_name_prefixed', '')}\n"
                context_text += f"Score: {p.get('score', 0)}\n"
                context_text += f"Content: {p.get('selftext', '')[:200]}\n\n"
                
            system_prompt = (
                "You are Omnibot. You just searched Reddit. Synthesize an answer to the user's query "
                "based strictly on these Reddit posts. Cite subreddits if applicable. Be concise and use markdown."
            )
            api_messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Query: {query}\n\nResults:\n{context_text}"}]
            answer = await self.nvidia_client.chat_completion(messages=api_messages, temperature=0.4, max_tokens=2048, top_p=0.9)
            await status_msg.delete()
            await update.message.reply_text(answer, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception as e:
            await status_msg.edit_text(f"❌ *Failed to search Reddit.* \nError: `{str(e)}`", parse_mode="Markdown")

    async def setcookie_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Allows admins to dynamically configure authentication cookies."""
        if not update.message or len(context.args) < 2:
            await update.message.reply_text("❌ *Usage*: `/setcookie <twitter|reddit> <cookie_string>`", parse_mode="Markdown")
            return
            
        platform = context.args[0].lower()
        cookie_val = " ".join(context.args[1:])
        
        if platform == "twitter":
            try:
                subprocess.run(["agent-reach", "configure", "twitter-cookies", cookie_val], check=True, capture_output=True)
                await update.message.reply_text("✅ *Twitter cookie successfully configured!*", parse_mode="Markdown")
            except Exception as e:
                await update.message.reply_text(f"❌ *Failed to configure Twitter cookie.* \nError: `{str(e)}`", parse_mode="Markdown")
        elif platform == "reddit":
            await update.message.reply_text("⚠️ *Reddit cookie configuration is not natively supported by our backend yet.* We are using the public JSON API instead.", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Unsupported platform. Use `twitter` or `reddit`.", parse_mode="Markdown")
