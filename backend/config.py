"""Configuration for the LLM Council."""

import os
import sys
from dotenv import load_dotenv

from dotenv import find_dotenv
env_path = find_dotenv()
print(f"[Config] Loading .env from: {env_path if env_path else 'NOT FOUND'}")
load_dotenv(env_path)

# Provider API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
XAI_API_KEY = os.getenv("XAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Debug: verify API keys loaded correctly at startup
print(f"[Config] ANTHROPIC_API_KEY loaded: {ANTHROPIC_API_KEY[:15] + '...' + ANTHROPIC_API_KEY[-4:] if ANTHROPIC_API_KEY and len(ANTHROPIC_API_KEY) > 19 else 'NOT SET'}")

# Legacy OpenRouter API key (for backward compatibility)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Model definitions with their required API keys
# Format: (model_id, api_key) - provider is extracted from model_id prefix
_MODEL_DEFINITIONS = [
    ("openai/gpt-5.2", OPENAI_API_KEY),
    ("google/gemini-2.0-flash", GOOGLE_API_KEY),
    ("anthropic/claude-sonnet-4-5", ANTHROPIC_API_KEY),
    ("x-ai/grok-4", XAI_API_KEY),
    ("groq/llama-3.3-70b-versatile", GROQ_API_KEY),
]

# Auto-filter: only include models with configured API keys
COUNCIL_MODELS = [model for model, api_key in _MODEL_DEFINITIONS if api_key]

# Log warning if some API keys are missing
_missing_providers = [model.split('/')[0] for model, api_key in _MODEL_DEFINITIONS if not api_key]
if _missing_providers:
    print(f"[Config] Missing API keys for: {', '.join(_missing_providers)} - these models will be excluded")

# Chairman model from .env or fallback to first available model
_env_chairman = os.getenv("CHAIRMAN_MODEL")
if _env_chairman:
    CHAIRMAN_MODEL = _env_chairman
elif COUNCIL_MODELS:
    CHAIRMAN_MODEL = COUNCIL_MODELS[0]
    print(f"[Config] CHAIRMAN_MODEL not set in .env, using first available model: {CHAIRMAN_MODEL}")
else:
    print("[Config] ERROR: No models available! Please configure at least one API key in .env", file=sys.stderr)
    CHAIRMAN_MODEL = None

# Title generation model from .env or fallback
_env_title_model = os.getenv("TITLE_GENERATION_MODEL")
if _env_title_model:
    TITLE_GENERATION_MODEL = _env_title_model
elif OPENAI_API_KEY:
    # Use lightweight GPT model for title generation (fast and cheap)
    TITLE_GENERATION_MODEL = "openai:gpt-4o-mini"
elif COUNCIL_MODELS:
    TITLE_GENERATION_MODEL = COUNCIL_MODELS[0]
else:
    TITLE_GENERATION_MODEL = None

# Provider-specific settings
PROVIDER_SETTINGS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "timeout": 120.0,
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com",
        "timeout": 120.0,
        "max_tokens": 4096,
    },
    "google": {
        "timeout": 120.0,
        "max_tokens": 8192,
    },
    "xai": {
        "base_url": "https://api.x.ai/v1",
        "timeout": 120.0,
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "timeout": 120.0,
    },
}

# Legacy OpenRouter API endpoint (for backward compatibility)
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"
