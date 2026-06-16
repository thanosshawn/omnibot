import requests
import asyncio
from typing import List, Dict, Any
import config

class NvidiaClient:
    """
    Client for interacting with NVIDIA's hosted Minimax-M3 model.
    Handles standard text chat as well as multimodal content (images/videos).
    """
    def __init__(self):
        self.api_key = config.NVIDIA_API_KEY
        self.invoke_url = config.NVIDIA_INVOKE_URL
        self.model = "minimaxai/minimax-m3"

    def _send_request(self, messages: List[Dict[str, Any]], temperature: float, max_tokens: int, top_p: float) -> Dict[str, Any]:
        """
        Executes a synchronous POST request to the NVIDIA completions endpoint.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": False
        }
        
        response = requests.post(self.invoke_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()

    async def chat_completion(self, messages: List[Dict[str, Any]], temperature: float = 1.00, max_tokens: int = 4096, top_p: float = 0.95) -> str:
        """
        Asynchronously calls the NVIDIA Minimax-M3 model using an executor thread.
        
        Args:
            messages: List of chat messages (including text, images/videos as parts).
            temperature: Sampling temperature (0.0 to 1.0).
            max_tokens: Maximum response tokens.
            top_p: Nucleus sampling probability.
            
        Returns:
            The string response from the model.
        """
        try:
            # Run the blocking request in a thread pool to avoid blocking the asyncio loop
            result = await asyncio.to_thread(
                self._send_request,
                messages,
                temperature,
                max_tokens,
                top_p
            )
            
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    return choice["message"]["content"]
            
            return f"Error: Unexpected response structure: {result}"
        except requests.exceptions.HTTPError as e:
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = e.response.text
            return f"NVIDIA API HTTP Error ({e.response.status_code}): {error_detail}"
        except requests.exceptions.RequestException as e:
            return f"Connection Error: Failed to reach NVIDIA API. Detail: {str(e)}"
        except Exception as e:
            return f"Unexpected Error: {str(e)}"
