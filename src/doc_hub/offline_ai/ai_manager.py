import os, requests, traceback
from google.generativeai import configure, GenerativeModel

LOCAL_URL = "http://127.0.0.1:7860/generate"
GEMINI_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if GEMINI_KEY:
    try:
        configure(api_key=GEMINI_KEY)
    except Exception as e:
        print(f"⚠️ Gemini init failed: {e}")


def call_gemini(prompt: str) -> str:
    if not GEMINI_KEY:
        raise Exception("Gemini API key missing or invalid.")
    model = GenerativeModel("gemini-1.5-pro")
    return model.generate_content(prompt).text.strip()


def call_local(prompt: str) -> str:
    try:
        r = requests.post(
            LOCAL_URL,
            json={"prompt": prompt, "max_tokens": 400},
            timeout=180,
        )
        if r.ok:
            return r.json().get("text", "").strip()
        raise Exception(f"Local model HTTP {r.status_code}: {r.text}")
    except Exception as e:
        raise Exception(f"Local AI error: {e}")


def chat_response(prompt: str, model_choice: str) -> str:
    try:
        if model_choice.lower() == "gemini":
            return call_gemini(prompt)
        elif model_choice.lower() in ("mistral", "phi-2"):
            return call_local(prompt)
        else:
            raise Exception(f"Unknown model: {model_choice}")
    except Exception as e1:
        print(f"[AI] {model_choice} failed: {e1}")
        try:
            if model_choice.lower() == "gemini":
                print("[AI] → Fallback: Phi-2")
                return call_local(prompt)
            elif model_choice.lower() in ("mistral", "phi-2"):
                if GEMINI_KEY:
                    print("[AI] → Fallback: Gemini")
                    return call_gemini(prompt)
                print("[AI] → Fallback: Phi-2 (local)")
                return call_local(prompt)
        except Exception as e2:
            print(f"[AI] All backends failed: {e2}")
            raise Exception("All AI backends failed.")


def summarize_doc(content: str) -> str:
    prompt = f"Summarize this document clearly and briefly:\n\n{content}"
    try:
        return call_gemini(prompt)
    except Exception as e:
        print(f"[AI] Gemini summarization failed: {e}")
        return call_local(prompt)
