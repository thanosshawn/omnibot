from typing import List, Dict, Any

class ChatSession:
    """
    Holds the state, configurations, and chat history for a specific Telegram chat.
    """
    def __init__(self, chat_id: int):
        self.chat_id = chat_id
        self.history: List[Dict[str, Any]] = []
        self.system_prompt: str = (
            "You are Omnibot, a powerful, helpful, and friendly AI assistant. "
            "You can answer questions, write code, analyze images and videos, and solve problems."
        )
        self.temperature: float = 1.00
        self.max_tokens: int = 4096
        self.top_p: float = 0.95
        self.group_memory: List[Dict[str, Any]] = []
        self.auto_reply: bool = False

    def clear_history(self):
        """Clears current conversation history."""
        self.history = []

    def clear_group_memory(self):
        """Clears the group memory buffer."""
        self.group_memory = []

    def add_group_message(self, sender: str, text: str):
        """Adds a message to the rolling group memory buffer, keeping the last 50 messages."""
        self.group_memory.append({"sender": sender, "text": text})
        if len(self.group_memory) > 50:
            self.group_memory = self.group_memory[-50:]

    def get_group_transcript(self) -> str:
        """Formats the current group memory buffer as a readable transcript."""
        if not self.group_memory:
            return "No recent messages in group memory."
        lines = []
        for msg in self.group_memory:
            lines.append(f"[{msg['sender']}]: {msg['text']}")
        return "\n".join(lines)

    def add_message(self, role: str, content: Any):
        """
        Adds a message to the chat history.
        
        Args:
            role: 'user' or 'assistant'.
            content: String (text) or List of dicts (multimodal content).
        """
        self.history.append({"role": role, "content": content})
        # Slide window to prevent context overflow (keep last 20 messages)
        if len(self.history) > 20:
            self.history = self.history[-20:]

    def get_messages_for_api(self) -> List[Dict[str, Any]]:
        """
        Prepares the list of messages, incorporating the current system prompt with styling rules.
        """
        messages = []
        if self.system_prompt:
            # We append style guidelines to ensure responses are decorated with emojis, bold headers, and structured lists
            style_guideline = (
                "\n\nStyle & Formatting Guidelines:\n"
                "- Decorate your response using relevant emojis to start paragraphs, key points, or responses.\n"
                "- Use bold headers, clean bullet points, and syntax-highlighted code blocks for maximum readability.\n"
                "- Ensure your layout looks visually polished, premium, and structured in a Telegram chat."
            )
            full_prompt = self.system_prompt
            if "Style & Formatting Guidelines:" not in full_prompt:
                full_prompt += style_guideline
            messages.append({"role": "system", "content": full_prompt})
            
        # If there is group chat memory, inject it to give the bot context of the recent discussion flow
        if self.group_memory:
            transcript = self.get_group_transcript()
            messages.append({
                "role": "system",
                "content": (
                    "Recent group conversation context (for situational awareness):\n"
                    "Use this to understand what users were talking about before querying you.\n"
                    "---------\n"
                    f"{transcript}\n"
                    "---------"
                )
            })

        messages.extend(self.history)
        return messages


class SessionManager:
    """
    Orchestrates and retrieves chat sessions for different chat ids.
    """
    def __init__(self):
        self.sessions: Dict[int, ChatSession] = {}

    def get_session(self, chat_id: int) -> ChatSession:
        """
        Gets the existing session or creates a new one for the given chat_id.
        """
        if chat_id not in self.sessions:
            self.sessions[chat_id] = ChatSession(chat_id)
        return self.sessions[chat_id]
