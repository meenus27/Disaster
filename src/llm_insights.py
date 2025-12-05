import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
USE_OPENROUTER = os.getenv("USE_OPENROUTER", "false").lower() == "true"

CACHE_PATH = Path("data/cached_advisories.json")
LOCAL_CACHE = {}
OPENAI_DISABLED = False

if CACHE_PATH.exists():
    try:
        with open(CACHE_PATH, encoding="utf-8") as f:
            LOCAL_CACHE = json.load(f)
    except Exception:
        LOCAL_CACHE = {}

def generate_advisory(severity, drivers, role="Authority"):
    global OPENAI_DISABLED
    prompt = f"Provide a concise advisory for severity={severity}. Drivers: {', '.join(drivers)}. Role: {role}."
    if OPENAI_DISABLED:
        return LOCAL_CACHE.get(severity, f"[Cached Advisory] {severity}: follow local instructions.")

    try:
        if USE_OPENROUTER and OPENROUTER_KEY:
            client = OpenAI(api_key=OPENROUTER_KEY, base_url="https://openrouter.ai/api/v1")
            model = "openai/gpt-3.5-turbo"
        elif OPENAI_KEY:
            client = OpenAI(api_key=OPENAI_KEY)
            model = "gpt-3.5-turbo"
        else:
            return LOCAL_CACHE.get(severity, f"[Mock Advisory] Severity: {severity}. Drivers: {', '.join(drivers)}")

        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a disaster authority generating advisories."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
        )
        text = resp.choices[0].message.content.strip()

        LOCAL_CACHE[severity] = text
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(LOCAL_CACHE, f, indent=2, ensure_ascii=False)

        return text

    except Exception as e:
        msg = str(e).lower()
        if "quota" in msg or "insufficient_quota" in msg:
            OPENAI_DISABLED = True
        print("LLM advisory error:", e)
        return LOCAL_CACHE.get(severity, f"[Mock Advisory] Severity: {severity}. Drivers: {', '.join(drivers)}")
