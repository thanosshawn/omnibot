from telegram.ext import Application
from nvidia_client import NvidiaClient
from session import SessionManager

class BaseModule:
    """
    Base class that all bot modules should inherit from.
    Provides standard references to the Telegram bot Application,
    the Nvidia Client, and the Session Manager.
    """
    def __init__(self, bot_app: Application, nvidia_client: NvidiaClient, session_manager: SessionManager):
        self.bot_app = bot_app
        self.nvidia_client = nvidia_client
        self.session_manager = session_manager

    def register(self):
        """
        Register handlers for this module.
        Must be overridden by subclasses.
        """
        raise NotImplementedError("Modules must implement the register() method.")
