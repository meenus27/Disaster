"""
Simple translation helper for CrowdShield.
Uses googletrans for demo purposes.

Some versions of googletrans expose `Translator.translate` as an async
coroutine; others are synchronous. This wrapper handles both so that
callers can treat it as a simple blocking function.
"""

import asyncio
import inspect

from googletrans import Translator

translator = Translator()


def _ensure_result(result):
    """Resolve coroutine results if needed and return the final object."""
    if inspect.iscoroutine(result):
        try:
            # If no event loop is running, create one via asyncio.run
            return asyncio.run(result)
        except RuntimeError:
            # Fallback: use existing event loop if already running
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(result)
    return result


def translate(text, dest="en"):
    """
    Translate text into the target language.
    Returns translated string, or original text if translation fails.
    """
    try:
        raw = translator.translate(text, dest=dest)
        result = _ensure_result(raw)
        # Some implementations may return the original text directly
        return getattr(result, "text", text if isinstance(result, str) else text)
    except Exception as e:
        print("Translation error:", e)
        return text
