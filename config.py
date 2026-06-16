import os
from dotenv import load_dotenv

# Load variables from .env if it exists
load_dotenv()

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# NVIDIA API Configuration
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "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")
NVIDIA_INVOKE_URL = os.getenv("NVIDIA_INVOKE_URL", "https://integrate.api.nvidia.com/v1/chat/completions")

# Validate configuration
def check_config():
    errors = []
    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN is missing in environment or .env file.")
    if not NVIDIA_API_KEY:
        errors.append("NVIDIA_API_KEY is missing in environment or .env file.")
    return errors
