import os

import colorama

# Initialize colorama
# autoreset=True means that after each print statement with a color,
# the color will be reset to the default. This can simplify manual resets.
colorama.init(autoreset=True)


# --- ANSI Color Codes for Terminal Output (still useful for clarity) ---
class TermColors:
    RED = colorama.Fore.RED
    GREEN = colorama.Fore.GREEN
    RESET = colorama.Style.RESET_ALL
    YELLOW = colorama.Fore.YELLOW
    # BLUE = colorama.Fore.BLUE   # For file names in diff, if desired


# --- Configuration ---
OPEN_ROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
LLM_MODEL = "google/gemini-2.5-flash-preview"


# Context Management Configuration
# Keeps the system prompt + this many recent user/assistant/tool messages.
# Adjust based on typical message size and model context limit.
# Each "item" is one message object in the list.
MAX_HISTORY_ITEMS = 30
# (user+assistant or user+assistant+tool+assistant)
