#!/usr/bin/env python3
"""
src/tts.py

Offline-first TTS helper:
 - pyttsx3 primary (no network)
 - gTTS secondary (with retries/backoff)
 - caching by text+lang hash
 - text fallback if audio cannot be produced

Returns: path to generated file (MP3 preferred) or path to a .txt fallback.
"""

from pathlib import Path
import hashlib
import logging
import time
import tempfile

# Try imports
try:
    import pyttsx3
except Exception:
    pyttsx3 = None

try:
    from gtts import gTTS
except Exception:
    gTTS = None

ALERTS_DIR = Path("data/alerts")
ALERTS_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("crowdshield.tts")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)


def _hash_text_lang(text: str, lang: str) -> str:
    h = hashlib.sha256()
    h.update(text.encode("utf-8"))
    h.update(b"||")
    h.update(lang.encode("utf-8"))
    return h.hexdigest()[:16]


def _safe_mp3_path(hash_key: str, lang: str) -> Path:
    name = f"tts_{lang}_{hash_key}.mp3"
    return ALERTS_DIR / name


def _try_pyttsx3(text: str, lang: str, out_path: Path) -> bool:
    if pyttsx3 is None:
        logger.debug("pyttsx3 not installed.")
        return False
    try:
        engine = pyttsx3.init()
        try:
            voices = engine.getProperty("voices")
            selected = None
            for v in voices:
                try:
                    if hasattr(v, "languages") and v.languages:
                        if any(str(lang).lower() in str(l).lower() for l in v.languages):
                            selected = v.id
                            break
                except Exception:
                    pass
                if lang.lower() in str(getattr(v, "name", "")).lower() or lang.lower() in str(getattr(v, "id", "")).lower():
                    selected = v.id
                    break
            if selected:
                engine.setProperty("voice", selected)
        except Exception:
            pass
        engine.save_to_file(text, str(out_path))
        engine.runAndWait()
        if out_path.exists() and out_path.stat().st_size > 0:
            logger.info("pyttsx3 generated audio: %s", out_path)
            return True
        else:
            logger.warning("pyttsx3 produced no file or empty file.")
            return False
    except Exception as e:
        logger.warning("pyttsx3 generation failed: %s", e)
        return False


def _try_gtts(text: str, lang: str, out_path: Path, max_retries: int = 3, base_delay: float = 1.0) -> bool:
    if gTTS is None:
        logger.debug("gTTS not available.")
        return False
    attempt = 0
    while attempt < max_retries:
        try:
            attempt += 1
            logger.info("gTTS attempt %d/%d for lang=%s", attempt, max_retries, lang)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tf:
                temp_path = Path(tf.name)
            try:
                tts = gTTS(text=text, lang=lang)
                tts.save(str(temp_path))
                temp_path.replace(out_path)
                logger.info("gTTS succeeded, wrote %s", out_path)
                return True
            except Exception as e:
                try:
                    if temp_path.exists():
                        temp_path.unlink()
                except Exception:
                    pass
                raise e
        except Exception as e:
            logger.warning("gTTS generation failed (attempt %d): %s", attempt, e)
            delay = base_delay * (2 ** (attempt - 1))
            time.sleep(delay)
    logger.warning("gTTS exhausted retries and failed.")
    return False


def generate_tts(text: str, lang: str = "en", filename: str | None = None) -> str:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string")
    text = text.strip()
    lang = (lang or "en").strip()
    if filename:
        out_path = Path(filename)
        if out_path.suffix.lower() != ".mp3":
            out_path = out_path.with_suffix(".mp3")
    else:
        key = _hash_text_lang(text, lang)
        out_path = _safe_mp3_path(key, lang)
    if out_path.exists() and out_path.stat().st_size > 0:
        logger.info("Using cached TTS file: %s", out_path)
        return str(out_path)
    try:
        ok = _try_pyttsx3(text, lang, out_path)
        if ok:
            return str(out_path)
    except Exception as e:
        logger.warning("pyttsx3 attempt raised unexpected exception: %s", e)
    try:
        ok2 = _try_gtts(text, lang, out_path)
        if ok2:
            return str(out_path)
    except Exception as e:
        logger.warning("gTTS attempt raised unexpected exception: %s", e)
    try:
        txt_path = out_path.with_suffix(".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
            f.write("\n\n")
            f.write(f"(TTS unavailable for lang='{lang}'; generated as text fallback)\n")
        logger.info("TTS fallback: wrote text advisory to %s", txt_path)
        return str(txt_path)
    except Exception as e:
        logger.error("Failed to write TTS fallback text file: %s", e)
        return text
