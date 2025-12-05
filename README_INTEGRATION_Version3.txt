```markdown
# CrowdShield — Integration Guide (Windows Command Prompt)

This integration guide shows exactly where to add API keys and tokens, step‑by‑step Windows Command Prompt commands to integrate services, and links to the sites you will need (OpenAI, Twilio, Google Cloud, etc.). Follow the recommended approach (use `.env`) — only use direct code edits if you understand the security implications.

Important security note
- Do NOT commit secrets to Git. Use `.env` or system environment variables.
- For demos, prefer leaving keys unset and using the built-in cached/mock fallbacks.

Contents
- Recommended placement for keys (best practice)
- Files that read secrets (exact files & where they look)
- How to populate `.env` (Windows cmd steps)
- Windows Command Prompt commands (temporary and persistent)
- Convenience step-by-step to integrate everything (Windows cmd)
- How to test each integration from Command Prompt
- Links & pages to obtain API keys
- Optional: where to hardcode keys in code (NOT recommended) — exact snippets
- Where to put Google Cloud credentials (if adapting TTS)
- Troubleshooting tips (Windows-specific)
- Quick checklist

1) Recommended placement for keys (best practice)
-----------------------------------------------
- Put all API keys and tokens in a `.env` file at the project root (same folder as `app.py`) OR set them as Windows environment variables.
- Copy the example in cmd:
```
copy .env.example .env
```
- Edit `.env` using Notepad so it is not accidentally committed:
```
notepad .env
```
- Paste the keys and save.

2) Files that read secrets (exact files & where they look)
-----------------------------------------------------------------
You generally do NOT need to edit code — populate `.env` and run the app. The following source files read env vars:

- crowdshield/src/llm_insights.py
  - Searches for:
    ```
    key = os.getenv("OPENAI_API_KEY")
    ```
  - Behavior: If key present and openai package available, it calls OpenAI ChatCompletion and caches results.

- crowdshield/src/alerting.py
  - Searches for:
    ```
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_num = os.getenv("TWILIO_FROM_NUMBER")
    to = to or os.getenv("TWILIO_TO_NUMBER")
    ```
  - Behavior: If any are missing, Twilio send is bypassed and mock_alert/satellite fallback is used.

- crowdshield/src/tts.py and crowdshield/src/translate.py
  - gTTS & googletrans do not need keys by default. If you integrate Google Cloud TTS, set `GOOGLE_APPLICATION_CREDENTIALS`.

3) How to populate `.env` (Windows cmd)
----------------------------------------
From the project root (the folder containing `app.py`):

1. Copy example `.env`:
```
copy .env.example .env
```

2. Open and edit:
```
notepad .env
```
3. Paste values (example):
```
OPENAI_API_KEY=sk-REPLACE_WITH_YOUR_KEY
TWILIO_ACCOUNT_SID=ACXXXXXXXXXXXXXXXXXXXXXXXXXXXX
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_FROM_NUMBER=+15005550006
TWILIO_TO_NUMBER=+919XXXXXXXXX
```
4. Save and close Notepad.

4) Windows Command Prompt — set environment variables
----------------------------------------------------
Two options: temporary (set) or persistent (setx).

A. Temporary for current cmd session (good for testing):
```
set OPENAI_API_KEY=sk-XXXXXXXXXXXXXXXXXXXX
set TWILIO_ACCOUNT_SID=ACXXXXXXXXXXXXXXXXXXXXXXXXXXXX
set TWILIO_AUTH_TOKEN=your_twilio_auth_token
set TWILIO_FROM_NUMBER=+15005550006
set TWILIO_TO_NUMBER=+919XXXXXXXXX

streamlit run app.py
```
- These variables exist only in the current Command Prompt window.

B. Persistent across sessions (use setx; opens new session to take effect):
```
setx OPENAI_API_KEY "sk-XXXXXXXXXXXXXXXXXXXX"
setx TWILIO_ACCOUNT_SID "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
setx TWILIO_AUTH_TOKEN "your_twilio_auth_token"
setx TWILIO_FROM_NUMBER "+15005550006"
setx TWILIO_TO_NUMBER "+919XXXXXXXXX"
```
- After setx, open a new Command Prompt window to use them.

5) Convenience step-by-step to integrate everything (Windows cmd)
-----------------------------------------------------------------
Assuming your current directory is the project root (the folder that contains `app.py`):

A. Create and activate virtual environment (cmd.exe):
```
python -m venv .venv
.venv\Scripts\activate.bat
```

B. Upgrade pip and install requirements:
```
python -m pip install --upgrade pip
pip install -r requirements.txt
```

C. Copy and edit `.env`:
```
copy .env.example .env
notepad .env
```
(Paste keys, save.)

D. Optional: Pre-download the OSMnx graph to avoid first-run delay:
```
python -c "from src import routing; routing.load_graph(online=True)"
```
This will create `data/local_graph.graphml`.

E. Run the Streamlit app:
```
streamlit run app.py
```

6) How to test each integration from Command Prompt
---------------------------------------------------
A. Test OpenAI access (quick check):
- If not using `.env`, set key temporarily:
```
set OPENAI_API_KEY=sk-REPLACE
```
- Run:
```
python -c "from src import llm_insights; print(llm_insights.generate_advisory('High',['flood','crowd'],'Local Authority'))"
```

B. Test Twilio SMS send:
- If not using `.env`, set values temporarily:
```
set TWILIO_ACCOUNT_SID=ACREPLACE
set TWILIO_AUTH_TOKEN=TOKENREPLACE
set TWILIO_FROM_NUMBER=+15005550006
set TWILIO_TO_NUMBER=+919XXXXXXXXX
```
- Run:
```
python -c "from src import alerting; print(alerting.send_twilio_sms('Test message from CrowdShield'))"
```
- The function returns a tuple: (True, messageSid) on success or (False, reason) on failure.

C. Test TTS generation (gTTS):
```
python -c "from src import tts; print(tts.generate_tts('എന്റെ പേര് CrowdShield ആണ്','ml'))"
```
- This saves an MP3 in `data/alerts/` and prints the path.

7) Links & exact pages for obtaining API keys and help
------------------------------------------------------
OpenAI (ChatGPT / API)
- Sign up & API keys: https://platform.openai.com/
- API keys page: https://platform.openai.com/account/api-keys
- Docs: https://platform.openai.com/docs

Twilio (SMS)
- Sign up & trial: https://www.twilio.com/try-twilio
- Console (Account SID & Auth Token): https://www.twilio.com/console
- SMS docs: https://www.twilio.com/docs/sms
- Quickstart (Python): https://www.twilio.com/docs/sms/quickstart/python

Google Cloud Text-to-Speech (optional)
- Console: https://console.cloud.google.com/
- Docs: https://cloud.google.com/text-to-speech/docs
- If using Google Cloud credentials: set `GOOGLE_APPLICATION_CREDENTIALS` to the JSON key path:
```
setx GOOGLE_APPLICATION_CREDENTIALS "C:\path\to\service-account.json"
```

gTTS (community wrapper)
- PyPI: https://pypi.org/project/gTTS/
- Docs: https://gtts.readthedocs.io/

OpenStreetMap and OSMnx
- OpenStreetMap: https://www.openstreetmap.org/
- OSMnx docs: https://osmnx.readthedocs.io/en/stable/

GeoPandas (docs & install help)
- GeoPandas: https://geopandas.org/

Streamlit & Folium
- Streamlit: https://docs.streamlit.io/
- Folium: https://python-visualization.github.io/folium/

8) Optional — Hardcoding keys in code (NOT recommended)
--------------------------------------------------------
If you absolutely must hardcode keys (temporary demo), here are exact places and snippets. NEVER commit after doing this.

A. Hardcode OpenAI key
File: `crowdshield/src/llm_insights.py`
Find:
```python
key = os.getenv("OPENAI_API_KEY")
```
Replace with:
```python
key = "sk-REPLACE_WITH_YOUR_KEY"
```

B. Hardcode Twilio values
File: `crowdshield/src/alerting.py`
Find:
```python
sid = os.getenv("TWILIO_ACCOUNT_SID")
token = os.getenv("TWILIO_AUTH_TOKEN")
from_num = os.getenv("TWILIO_FROM_NUMBER")
to = to or os.getenv("TWILIO_TO_NUMBER")
```
Replace with:
```python
sid = "ACREPLACE_WITH_YOUR_SID"
token = "REPLACE_WITH_YOUR_TOKEN"
from_num = "+15005550006"
to = to or "+919XXXXXXXXX"
```

Cautions:
- Remove hardcoded keys before sharing or committing.
- Prefer using `.env` and `os.getenv()`.

9) Where to place Google Cloud credentials (if adapting TTS to GCP)
-------------------------------------------------------------------
- Create service account with Text-to-Speech enabled and download JSON key (e.g., `C:\keys\gcp-tts.json`).
- Set environment variable (persistent):
```
setx GOOGLE_APPLICATION_CREDENTIALS "C:\keys\gcp-tts.json"
```
- Or temporary:
```
set GOOGLE_APPLICATION_CREDENTIALS=C:\keys\gcp-tts.json
```

10) Troubleshooting tips (Windows-specific)
-------------------------------------------
- After `setx`, open a new cmd window to see variables (they do not appear in the current session).
- To echo an env var in cmd:
```
echo %OPENAI_API_KEY%
```
- If `streamlit` or Python cannot import `src`, ensure you run from the project root (the folder that contains `app.py` and the `src` folder) and that `src\__init__.py` exists.
- If `pip install` fails for geopandas/osmnx: use conda and conda-forge (Anaconda Prompt) to install prebuilt wheels.
- If OSMnx graph download stalls: check firewall/proxy, or run the predownload command on a different network.

11) Quick Windows checklist
---------------------------
From project root in Command Prompt:
```
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
notepad .env         (paste keys, save)
python -c "from src import routing; routing.load_graph(online=True)"   (optional predownload)
streamlit run app.py
```

12) Example `.env` (do NOT commit)
```
OPENAI_API_KEY=sk-REPLACE_WITH_YOUR_KEY
TWILIO_ACCOUNT_SID=ACXXXXXXXXXXXXXXXXXXXXXXXXXXXX
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_FROM_NUMBER=+15005550006
TWILIO_TO_NUMBER=+919XXXXXXXXX
```

13) If you want next
- I can produce a PowerShell (.ps1) variant that uses `Set-Item Env:` and `Start-Process` to launch Streamlit.
- I can produce a small `.bat` file that temporarily sets env vars (unsafe for long-term) and launches Streamlit for demo use.
- I can provide exact line numbers in your local files if you paste the output of:
```
findstr /n /c:"OPENAI_API_KEY" src\*.py
findstr /n /c:"TWILIO_ACCOUNT_SID" src\*.py
```

Tell me which optional item you want and I will generate it.
```