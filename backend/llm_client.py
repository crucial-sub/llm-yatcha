"""Multi-provider LLM client for OpenAI, Anthropic, and Google APIs."""

import asyncio
import httpx
from typing import List, Dict, Any, Optional
from .config import OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, XAI_API_KEY, GROQ_API_KEY


async def _query_openai(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """
    Query OpenAI API.

    Args:
        model: Model name (without provider prefix)
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content', or None if failed
    """
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            message = data['choices'][0]['message']

            return {
                'content': message.get('content'),
            }

    except Exception as e:
        print(f"Error querying OpenAI model {model}: {e}")
        return None


async def _query_anthropic(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """
    Query Anthropic API.

    Args:
        model: Model name (without provider prefix)
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content', or None if failed
    """

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    # Anthropic API requires max_tokens
    payload = {
        "model": model,
        "max_tokens": 8192,
        "messages": messages,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            # Anthropic returns content as array of content blocks
            content_blocks = data.get('content', [])
            text_content = ""
            for block in content_blocks:
                if block.get('type') == 'text':
                    text_content += block.get('text', '')

            return {
                'content': text_content,
            }

    except httpx.HTTPStatusError as e:
        error_body = e.response.text if e.response else "No response body"
        print(f"Error querying Anthropic model {model}: {e}")
        print(f"Anthropic error details: {error_body}")
        return None
    except Exception as e:
        print(f"Error querying Anthropic model {model}: {e}")
        return None


async def _query_google(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """
    Query Google Gemini API.

    Args:
        model: Model name (without provider prefix)
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content', or None if failed
    """
    # Convert OpenAI-style messages to Gemini format
    contents = []
    for msg in messages:
        role = "user" if msg['role'] == 'user' else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg['content']}]
        })

    payload = {
        "contents": contents,
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GOOGLE_API_KEY}"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                url,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            # Extract text from Gemini response
            candidates = data.get('candidates', [])
            if candidates:
                parts = candidates[0].get('content', {}).get('parts', [])
                if parts:
                    return {
                        'content': parts[0].get('text', ''),
                    }

            return {'content': ''}

    except Exception as e:
        print(f"Error querying Google model {model}: {e}")
        return None


async def _query_xai(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """
    Query xAI (Grok) API - OpenAI compatible.

    Args:
        model: Model name (without provider prefix)
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content', or None if failed
    """
    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            message = data['choices'][0]['message']

            return {
                'content': message.get('content'),
            }

    except Exception as e:
        print(f"Error querying xAI model {model}: {e}")
        return None


async def _query_groq(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """
    Query Groq API - OpenAI compatible.

    Args:
        model: Model name (without provider prefix)
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content', or None if failed
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            message = data['choices'][0]['message']

            return {
                'content': message.get('content'),
            }

    except Exception as e:
        print(f"Error querying Groq model {model}: {e}")
        return None


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """
    Query a model via the appropriate provider API.

    Args:
        model: Model identifier with provider prefix (e.g., "openai/gpt-4o")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content', or None if failed
    """
    # Parse provider and model name (support both / and : separators)
    if '/' in model:
        provider, model_name = model.split('/', 1)
    elif ':' in model:
        provider, model_name = model.split(':', 1)
    else:
        print(f"Invalid model format (missing provider prefix): {model}")
        return None

    # Normalize provider names
    provider = provider.lower()
    if provider == 'x-ai':
        provider = 'xai'

    if provider == 'openai':
        return await _query_openai(model_name, messages, timeout)
    elif provider == 'anthropic':
        return await _query_anthropic(model_name, messages, timeout)
    elif provider == 'google':
        return await _query_google(model_name, messages, timeout)
    elif provider == 'xai':
        return await _query_xai(model_name, messages, timeout)
    elif provider == 'groq':
        return await _query_groq(model_name, messages, timeout)
    else:
        print(f"Unknown provider: {provider}")
        return None


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]]
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models in parallel.

    Args:
        models: List of model identifiers with provider prefix
        messages: List of message dicts to send to each model

    Returns:
        Dict mapping model identifier to response dict (or None if failed)
    """
    # Create tasks for all models
    tasks = [query_model(model, messages) for model in models]

    # Wait for all to complete
    responses = await asyncio.gather(*tasks)

    # Map models to their responses
    return {model: response for model, response in zip(models, responses)}
