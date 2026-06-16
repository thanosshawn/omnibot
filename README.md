# 🤖 Omnibot - Multimodal AI Telegram Bot

Omnibot is a production-ready, modular Telegram bot powered by NVIDIA's hosted **Minimax-M3** multimodal AI. It supports conversational memory, dynamic settings adjustments, real-time web searches, native interactive quizzes, and multimodal image/video analysis.

---

## 🏗️ Architecture: "What Thing Does What"

Here is a breakdown of the project files and directories, explaining their specific responsibilities.

### Core Architecture Files
*   **[`main.py`](file:///c:/Users/karti/OneDrive/Desktop/code/omnibot/main.py)**: The central application runner. It:
    1. Sets up system logging.
    2. Validates environment configurations.
    3. Dynamically loads and registers all plugin modules from the `modules/` folder.
    4. Automatically detects whether it is running locally or on Render (using environment variables `RENDER_EXTERNAL_HOSTNAME` and `PORT`) and starts either **Webhook mode** (for production) or **Polling mode** (for local development).
*   **[`config.py`](file:///c:/Users/karti/OneDrive/Desktop/code/omnibot/config.py)**: Manages environment configuration. It loads variables from a `.env` file (if present) or system variables, validating that `TELEGRAM_BOT_TOKEN` and `NVIDIA_API_KEY` are provided.
*   **[`nvidia_client.py`](file:///c:/Users/karti/OneDrive/Desktop/code/omnibot/nvidia_client.py)**: The integration wrapper for NVIDIA's AI completions. It makes asynchronous, non-blocking HTTP requests to the Minimax-M3 model for text completions, base64-encoded image questions, and video queries.
*   **[`session.py`](file:///c:/Users/karti/OneDrive/Desktop/code/omnibot/session.py)**: State manager for Telegram chats. It maintains a separate `ChatSession` for each unique chat ID, tracking conversation history (using a 20-message sliding window to avoid context limits), system prompt configurations, temperature, top_p, and token thresholds.
*   **[`requirements.txt`](file:///c:/Users/karti/OneDrive/Desktop/code/omnibot/requirements.txt)**: Lists all Python package dependencies required by the application.
*   **[`render.yaml`](file:///c:/Users/karti/OneDrive/Desktop/code/omnibot/render.yaml)**: A Render Blueprint configuration file that allows for quick, single-click deployment of the bot as a Render Web Service.

### The Modular Plugins (`modules/` Directory)
The bot uses a dynamic registry system. Any class inheriting from `BaseModule` inside the `modules/` folder is automatically loaded at startup:
*   **[`modules/__init__.py`](file:///c:/Users/karti/OneDrive/Desktop/code/omnibot/modules/__init__.py)**: Scans the `modules/` folder at startup, instantiates all matching plugin modules, and invokes their `register()` methods.
*   **[`modules/base.py`](file:///c:/Users/karti/OneDrive/Desktop/code/omnibot/modules/base.py)**: Defines `BaseModule`, providing core hooks for interacting with the Telegram Application, Nvidia API client, and session manager.
*   **[`modules/core.py`](file:///c:/Users/karti/OneDrive/Desktop/code/omnibot/modules/core.py)**: Defines the essential system-level commands:
    *   `/start` - Clears the session state and sends a visual welcome greeting.
    *   `/help` - Lists all available user options and commands.
*   **[`modules/chat.py`](file:///c:/Users/karti/OneDrive/Desktop/code/omnibot/modules/chat.py)**: Manages general text conversations. It filters group messages (only replying if directly mentioned or replied to) and contains the `/clear` command to reset bot memory.
*   **[`modules/settings.py`](file:///c:/Users/karti/OneDrive/Desktop/code/omnibot/modules/settings.py)**: Exposes controls to adjust model behaviour dynamically within Telegram:
    *   `/system <prompt>` - Customizes the bot's system persona (e.g., `/system Speak like a pirate`).
    *   `/temperature <value>` - Adjusts generation temperature between `0.0` and `1.0`.
    *   `/info` - Details active session metrics (tokens, model, historical memory depth).
*   **[`modules/search.py`](file:///c:/Users/karti/OneDrive/Desktop/code/omnibot/modules/search.py)**: Integrates search capability:
    *   `/search <query>` - Executes an asynchronous, non-blocking DuckDuckGo query, extracts the top search results, and prompts Minimax-M3 to synthesize a detailed answer with inline Markdown citations.
*   **[`modules/multimodal.py`](file:///c:/Users/karti/OneDrive/Desktop/code/omnibot/modules/multimodal.py)**: Listens for image and video uploads. It downloads the file via the Telegram API, encodes it to base64, and feeds it to the AI for visual analysis based on your caption.
*   **[`modules/quiz.py`](file:///c:/Users/karti/OneDrive/Desktop/code/omnibot/modules/quiz.py)**: Command handler:
    *   `/quiz <topic>` - Dynamically builds multiple-choice questions on any subject via the model, parsing them into structured JSON, and outputs a native interactive Telegram Poll quiz with animations and explanation cards.

---

## 🚀 How to Deploy on Render

Render Web Services require port binding. By default, our bot will automatically deploy as an async web server using webhooks on Render (which satisfies the free-tier health check).

### Option A: Using Render Blueprints (Recommended)
1. Push your code repository to GitHub (ensure you don't commit your actual `.env` file).
2. Go to your **Render Dashboard**, click **New +**, and select **Blueprint**.
3. Link your GitHub repository.
4. Render will read the [`render.yaml`](file:///c:/Users/karti/OneDrive/Desktop/code/omnibot/render.yaml) configuration.
5. You will be prompted to enter the following configurations:
    *   `TELEGRAM_BOT_TOKEN`: Your bot token from `@BotFather`.
    *   `NVIDIA_API_KEY`: Your NVIDIA API key (`nvapi-...`).
6. Click **Apply**. Render will automatically build the bot and set up the webhook!

---

### Option B: Manual Web Service Setup
If you prefer to configure the Web Service manually:
1. Click **New +** -> **Web Service**.
2. Connect your GitHub repository.
3. Configure the following fields:
    *   **Name**: `omnibot`
    *   **Language**: `Python`
    *   **Branch**: `main` (or your active branch)
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `python main.py`
4. Add the following **Environment Variables** in the service settings:
    *   `TELEGRAM_BOT_TOKEN`: *your-telegram-token*
    *   `NVIDIA_API_KEY`: *your-nvidia-api-key*
    *   `NVIDIA_INVOKE_URL`: `https://integrate.api.nvidia.com/v1/chat/completions` (already set as default but good to verify)
5. Click **Create Web Service**. Render will spin up the container, assign a public hostname (e.g., `https://omnibot-xxxx.onrender.com`), and automatically trigger Webhook Mode!
