import requests
import json
import config

def test_connection():
    print(f"Targeting URL: {config.NVIDIA_INVOKE_URL}")
    print(f"Using API Key: {config.NVIDIA_API_KEY[:10]}...{config.NVIDIA_API_KEY[-5:] if len(config.NVIDIA_API_KEY) > 10 else ''}")
    
    headers = {
        "Authorization": f"Bearer {config.NVIDIA_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "minimaxai/minimax-m3",
        "messages": [{"role": "user", "content": "Respond in 3 words confirming you are alive."}],
        "max_tokens": 50,
        "temperature": 1.00,
        "top_p": 0.95,
        "stream": False,
    }

    print("Sending test request to NVIDIA Minimax-M3 endpoint...")
    try:
        response = requests.post(config.NVIDIA_INVOKE_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        print("\n[SUCCESS] Connection Successful!")
        print("Response payload:")
        data = response.json()
        print(json.dumps(data, indent=2))
        
        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0]["message"]["content"]
            print(f"\nAI Response: {content}")
    except requests.exceptions.HTTPError as e:
        print(f"\n[HTTP ERROR] ({e.response.status_code}):")
        try:
            print(json.dumps(e.response.json(), indent=2))
        except Exception:
            print(e.response.text)
    except Exception as e:
        print(f"\n[FAILED] Connection Failed: {e}")

if __name__ == "__main__":
    test_connection()
