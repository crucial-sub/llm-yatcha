# CLAUDE.md - Technical Notes for LLM Council

This file contains technical details, architectural decisions, and important implementation notes for future development sessions.

## Project Overview

LLM Council is a 3-stage deliberation system where multiple LLMs collaboratively answer user questions. The key innovation is anonymized peer review in Stage 2, preventing models from playing favorites.

## Architecture

### Backend Structure (`backend/`)

**`config.py`**
- Provider-specific API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, XAI_API_KEY)
- `COUNCIL_MODELS` - Uses `provider:model` format (e.g., `"openai:gpt-4o"`, `"anthropic:claude-sonnet-4-20250514"`)
- `CHAIRMAN_MODEL` - Specifies the chairman model for final synthesis
- `PROVIDER_SETTINGS` - Per-provider settings (timeout, base_url, max_tokens, etc.)
- Backend runs on **port 8001** (NOT 8000 - user had another app on 8000)

**`providers/`** - LLM Provider Implementations
- `base.py`: Abstract base class (BaseLLMProvider, LLMResponse dataclass)
- `openai_provider.py`: OpenAI API (GPT models, reasoning models support)
- `anthropic_provider.py`: Anthropic Messages API (Claude models, extended thinking support)
- `google_provider.py`: Google Generative AI (Gemini models)
- `xai_provider.py`: xAI API (Grok models, OpenAI-compatible)
- `__init__.py`: Provider registry and factory functions

**`llm_client.py`** (replaces openrouter.py)
- `query_model()`: Single model query (auto-detects or explicitly specified provider)
- `query_models_parallel()`: Parallel model queries using `asyncio.gather()`
- `parse_model_string()`: Parses `provider:model` format with auto-detection
- Provider instance caching for efficiency
- Maintains same interface as original openrouter.py (backward compatible)

**`council.py`** - The Core Logic
- `stage1_collect_responses()`: Parallel queries to all council models (supports conversation history context)
- `stage2_collect_rankings()`:
  - Anonymizes responses as "Response A, B, C, etc."
  - Creates `label_to_model` mapping for de-anonymization
  - Prompts models to evaluate and rank (with strict format requirements)
  - Returns tuple: (rankings_list, label_to_model_dict)
  - Each ranking includes both raw text and `parsed_ranking` list
- `stage3_synthesize_final()`: Chairman synthesizes from all responses + rankings
- `parse_ranking_from_text()`: Extracts "FINAL RANKING:" section, handles both numbered lists and plain format
- `calculate_aggregate_rankings()`: Computes average rank position across all peer evaluations
- `generate_conversation_title()`: Auto-generates conversation title from first question (supports Korean/English)

**`storage.py`**
- JSON-based conversation storage in `data/conversations/`
- Each conversation: `{id, created_at, title, messages[]}`
- Assistant messages contain: `{role, stage1, stage2, stage3}`
- `delete_conversation()`: Deletes a conversation
- `remove_last_assistant_message()`: Removes last assistant message for regeneration
- Note: metadata (label_to_model, aggregate_rankings) is NOT persisted to storage, only returned via API

**`main.py`**
- FastAPI app with CORS enabled for localhost:5173 and localhost:3000
- API Endpoints:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/conversations` | List all conversations |
| POST | `/api/conversations` | Create new conversation |
| GET | `/api/conversations/{id}` | Get conversation details |
| POST | `/api/conversations/{id}/message` | Send message (non-streaming) |
| POST | `/api/conversations/{id}/message/stream` | Send message (SSE streaming) |
| DELETE | `/api/conversations/{id}` | Delete conversation |
| POST | `/api/conversations/{id}/regenerate/stream` | Regenerate response (SSE streaming) |

### Frontend Structure (`frontend/src/`)

**`main.jsx`**
- Wraps app with ThemeProvider for dark mode support

**`context/ThemeContext.jsx`**
- Manages dark/light mode state
- Auto-detects system preference (`prefers-color-scheme`)
- Supports manual toggle
- Persists preference to localStorage

**`App.jsx`**
- Main orchestration: manages conversations list and current conversation
- Handles message sending, regeneration, and deletion
- Important: metadata is stored in the UI state for display but not persisted to backend JSON

**`api.js`**
- `listConversations()`, `createConversation()`, `getConversation()`
- `sendMessageStream()`: SSE streaming message send
- `regenerateStream()`: Regenerate response streaming
- `deleteConversation()`: Delete conversation

**`components/Sidebar.jsx`**
- Displays conversation list
- New conversation button
- Dark mode toggle button
- Conversation delete (vertical ellipsis menu on hover)
- Delete confirmation modal

**`components/ChatInterface.jsx`**
- Multiline textarea (3 rows, resizable)
- Enter to send, Shift+Enter for new line
- Always-visible input form (supports follow-up questions)
- Regenerate button (below last assistant message)
- User messages wrapped in markdown-content class for padding

**`components/Stage1.jsx`**
- Tab view of individual model responses
- ReactMarkdown rendering with markdown-content wrapper

**`components/Stage2.jsx`**
- **Critical Feature**: Tab view showing RAW evaluation text from each model
- De-anonymization happens CLIENT-SIDE for display (models receive anonymous labels)
- Shows "Extracted Ranking" below each evaluation so users can validate parsing
- Aggregate rankings shown with average position and vote count
- Explanatory text clarifies that boldface model names are for readability only

**`components/Stage3.jsx`**
- Final synthesized answer from chairman
- Green-tinted background to highlight conclusion
- **Copy button**: Copies final answer to clipboard (shows "Copied!" feedback for 2 seconds)

**Styling (`*.css`)**
- CSS variable-based theme system (dark/light mode)
- Primary color: `--accent-primary` (#4a90e2 light / #5a9fe2 dark)
- Global markdown styling in `index.css` with `.markdown-content` class
- 12px padding on all markdown content to prevent cluttered appearance

### CSS Variables (index.css)
```css
:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f8f8f8;
  --text-primary: #333333;
  --text-secondary: #666666;
  --border-primary: #e0e0e0;
  --accent-primary: #4a90e2;
  /* ... */
}

[data-theme="dark"] {
  --bg-primary: #1a1a1a;
  --bg-secondary: #242424;
  --text-primary: #e0e0e0;
  --text-secondary: #b0b0b0;
  --border-primary: #404040;
  --accent-primary: #5a9fe2;
  /* ... */
}
```

## Key Design Decisions

### Multi-Provider Architecture
- Provider abstraction for extensibility
- Encapsulates API format differences per provider:
  - OpenAI: Bearer token, standard chat completions
  - Anthropic: x-api-key header, Messages API, separate system prompt
  - Google: API key as query param, contents/parts structure
  - xAI: OpenAI-compatible API
- Auto-detection by model ID prefix or explicit specification (`provider:model`)

### Stage 2 Prompt Format
The Stage 2 prompt is very specific to ensure parseable output:
```
1. Evaluate each response individually first
2. Provide "FINAL RANKING:" header
3. Numbered list format: "1. Response C", "2. Response A", etc.
4. No additional text after ranking section
```

This strict format allows reliable parsing while still getting thoughtful evaluations.

### De-anonymization Strategy
- Models receive: "Response A", "Response B", etc.
- Backend creates mapping: `{"Response A": "openai:gpt-4o", ...}`
- Frontend displays model names in **bold** for readability
- Users see explanation that original evaluation used anonymous labels
- This prevents bias while maintaining transparency

### Error Handling Philosophy
- Continue with successful responses if some models fail (graceful degradation)
- Never fail the entire request due to single model failure
- Log errors but don't expose to user unless all models fail
- Per-provider error handling with consistent fallback behavior

### UI/UX Features
- **Copy Answer**: One-click copy from Stage3
- **Regenerate Answer**: Deletes last response and regenerates
- **Follow-up Questions**: Always-visible input, conversation history context passed to models
- **Delete Conversation**: Hover menu + confirmation dialog
- **Dark Mode**: System detection + manual toggle + localStorage persistence
- All raw outputs are inspectable via tabs
- Parsed rankings shown below raw text for validation

## Important Implementation Details

### Relative Imports
All backend modules use relative imports (e.g., `from .config import ...`) not absolute imports. This is critical for Python's module system to work correctly when running as `python -m backend.main`.

### Port Configuration
- Backend: 8001 (changed from 8000 to avoid conflict)
- Frontend: 5173 (Vite default)
- Update both `backend/main.py` and `frontend/src/api.js` if changing

### Markdown Rendering
All ReactMarkdown components must be wrapped in `<div className="markdown-content">` for proper spacing. This class is defined globally in `index.css`.

### Model Configuration
Models configured in `backend/config.py` using `provider:model` format:
```python
COUNCIL_MODELS = [
    "openai:gpt-4o",
    "anthropic:claude-sonnet-4-20250514",
    "google:gemini-2.0-flash",
    "xai:grok-2",
]
CHAIRMAN_MODEL = "google:gemini-2.0-flash"
```

### Theme System
- CSS variable-based (`--bg-primary`, `--text-primary`, etc.)
- Dark mode styles applied via `[data-theme="dark"]` selector
- ThemeContext calls `document.documentElement.setAttribute('data-theme', theme)`

## Common Gotchas

1. **Module Import Errors**: Always run backend as `python -m backend.main` from project root, not from backend directory
2. **CORS Issues**: Frontend must match allowed origins in `main.py` CORS middleware
3. **Ranking Parse Failures**: If models don't follow format, fallback regex extracts any "Response X" patterns in order
4. **Missing Metadata**: Metadata is ephemeral (not persisted), only available in API responses
5. **Provider API Key Missing**: Ensure each provider's API key is set in .env
6. **Model Format**: Must use `provider:model` format (e.g., `openai:gpt-4o`, `anthropic:claude-sonnet-4-20250514`)

## Environment Variables (.env)

```bash
# Multi-provider API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
XAI_API_KEY=xai-...

# Legacy (optional, for backward compatibility)
OPENROUTER_API_KEY=sk-or-...
```

## Testing Notes

Use `test_providers.py` to verify API connectivity for each provider:
```bash
python -m backend.test_providers
```

Tests individual provider queries and parallel queries across multiple providers.

## Data Flow Summary

```
User Query
    ↓
Stage 1: query_models_parallel(COUNCIL_MODELS) via llm_client
    ├─→ OpenAI Provider → GPT response
    ├─→ Anthropic Provider → Claude response
    ├─→ Google Provider → Gemini response
    └─→ xAI Provider → Grok response
    ↓
Stage 2: Anonymize → query_models_parallel(COUNCIL_MODELS)
    ├─→ Model A evaluates (sees: Response A, B, C, D as anonymous)
    ├─→ Model B evaluates
    ├─→ Model C evaluates
    └─→ Model D evaluates
    ↓ parse_ranking_from_text() + calculate_aggregate_rankings()
    ↓
Stage 3: query_model(CHAIRMAN_MODEL)
    └─→ Synthesized answer
    ↓
Return: {stage1, stage2, stage3, metadata}
    ↓
Frontend: Display with tabs + validation UI + copy/regenerate buttons
```

The entire flow is async/parallel where possible to minimize latency.
