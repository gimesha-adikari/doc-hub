import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv

try:
    import google.generativeai as genai
    _HAS_GENAI = True
except Exception:
    genai = None
    _HAS_GENAI = False


class AIService:
    def __init__(self):
        self.api_key = self.load_api_key()

        if not self.api_key:
            print("⚠️ GOOGLE_API_KEY not found. Please set it in Settings.")
            self.model = None
            self.chat = None
            return

        if not _HAS_GENAI:
            print("⚠️ google-generativeai not installed — AI features disabled.")
            self.model = None
            self.chat = None
            return

        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-2.5-flash")
            self.chat = self.model.start_chat(history=[])
            print("✅ AI Service initialized successfully.")
        except Exception as e:
            print(f"❌ Error initializing AI Service: {e}")
            self.model = None
            self.chat = None

    @staticmethod
    def load_api_key() -> str:
        found = load_dotenv()
        if not found:
            load_dotenv(os.path.expanduser("~/.doc-hub-env"))
        return os.getenv("GOOGLE_API_KEY")

    def get_response(self, document_content: str, user_question: str) -> str:
        if not self.model:
            return "⚠️ AI Service is not configured. Please check your API key in Settings."

        prompt = f"""
        Here is a document:
        ---
        {document_content}
        ---

        Answer the following question based *only* on the document provided:
        {user_question}
        """

        try:
            response = self.chat.send_message(prompt)
            return getattr(response, "text", str(response))
        except Exception as e:
            print(f"Error getting response from AI: {e}")
            try:
                # Fallback if chat fails
                if hasattr(self.model, "generate_content"):
                    resp = self.model.generate_content(prompt)
                    return getattr(resp, "text", str(resp))
            except Exception as inner_e:
                print(f"Fallback AI call failed: {inner_e}")
            return f"Error from AI: {e}"

    def get_tags_and_summary(self, document_content: str) -> (str, str):
        if not self.model:
            return "", ""

        truncated_content = document_content[:10000]

        prompt = f"""
        Analyze the document below and respond strictly in JSON.

        DOCUMENT:
        ---
        {truncated_content}
        ---

        JSON format:
        {{
            "summary": "one-sentence summary",
            "tags": ["keyword1", "keyword2", ...]
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            clean_text = (getattr(response, "text", str(response)) or "").strip()
            clean_text = clean_text.replace("```json", "").replace("```", "")
            match = re.search(r"\{.*}", clean_text, re.DOTALL)
            if not match:
                return "", ""
            data = json.loads(match.group(0))
            summary = data.get("summary", "").strip()
            tags_list = data.get("tags", [])
            tags_str = ", ".join(tags_list)
            return tags_str, summary
        except json.JSONDecodeError:
            print("⚠️ AI did not return valid JSON.")
            return "", ""
        except Exception as e:
            print(f"Error getting AI tags/summary: {e}")
            return "", ""

    def get_file_category(self, file_name: str, file_content: str) -> str:
        if not self.model:
            return "Uncategorized"

        categories = [
            "Invoices", "Receipts", "Documents", "Contracts", "Resumes",
            "Code", "Scripts", "Logs", "Databases",
            "Images", "Videos", "Audio",
            "Archives", "Installers", "Temporary",
            "Notes", "Books", "Other"
        ]

        ext = Path(file_name).suffix.lower()

        # Quick classification without AI
        if not file_content.strip():
            if ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"]:
                return "Images"
            elif ext in [".mp4", ".avi", ".mkv", ".mov", ".webm"]:
                return "Videos"
            elif ext in [".mp3", ".wav", ".flac", ".ogg", ".m4a"]:
                return "Audio"
            elif ext in [".zip", ".rar", ".7z", ".tar", ".gz"]:
                return "Archives"
            elif ext in [".exe", ".msi", ".appimage", ".deb", ".rpm"]:
                return "Installers"
            elif ext in [".log", ".tmp"]:
                return "Temporary"
            elif ext in [".py", ".java", ".js", ".ts", ".cpp", ".sh"]:
                return "Code"
            elif ext in [".txt", ".md", ".ini", ".cfg"]:
                return "Notes"
            else:
                return "Other"

        truncated = file_content[:2000]

        prompt = f"""
        You are a file organizer. Assign one category from:
        {", ".join(categories)}

        FILE NAME:
        {file_name}

        FILE CONTENT:
        ---
        {truncated}
        ---

        Respond only with the category name.
        """

        try:
            response = self.model.generate_content(prompt)
            category = (getattr(response, "text", str(response)) or "").strip().title()
            category = category.replace("Files", "").replace("File", "").strip()
            if category.endswith("s") and category[:-1] in categories:
                category = category[:-1]
            for c in categories:
                if category.lower().startswith(c.lower()):
                    return c
            return "Other"
        except Exception as e:
            print(f"Error getting AI category: {e}")
            return "Other"
