import importlib
import pkgutil
import inspect
from telegram.ext import Application
from nvidia_client import NvidiaClient
from session import SessionManager
from .base import BaseModule

def load_modules(bot_app: Application, nvidia_client: NvidiaClient, session_manager: SessionManager):
    """
    Dynamically loads all modules within the modules package that inherit from BaseModule.
    
    Args:
        bot_app: The telegram.ext.Application instance.
        nvidia_client: The NvidiaClient instance.
        session_manager: The SessionManager instance.
        
    Returns:
        A list of loaded module instances.
    """
    loaded = []
    # Find all modules (files and sub-directories) in the current package
    for _, module_name, _ in pkgutil.iter_modules(__path__, __name__ + "."):
        if module_name.endswith(".base"):
            continue
        try:
            # Import the module dynamically
            mod = importlib.import_module(module_name)
            
            # Look for subclasses of BaseModule inside the imported module
            for name, obj in inspect.getmembers(mod):
                if inspect.isclass(obj) and issubclass(obj, BaseModule) and obj is not BaseModule:
                    module_instance = obj(bot_app, nvidia_client, session_manager)
                    module_instance.register()
                    loaded.append(module_instance)
                    print(f"[Module Loader] Loaded: {name} from {module_name}")
        except Exception as e:
            print(f"[Module Loader] Failed to load module {module_name}: {e}")
            
    return loaded
