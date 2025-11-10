import os
from dotenv import load_dotenv
from src.doc_hub.offline_ai.ai_manager import chat_response, summarize_doc


class AIService:

    def __init__(self):
        self.api_key = self.load_api_key()
        self.model_choice = "Gemini"
        if not self.api_key:
            print("⚠️ GOOGLE_API_KEY not found. Local models will be used as fallback.")

    @staticmethod
    def load_api_key() -> str:
        found = load_dotenv()
        if not found:
            load_dotenv(os.path.expanduser("~/.doc-hub-env"))
        return os.getenv("GOOGLE_API_KEY")

    def get_response(self, document_content: str, user_question: str) -> str:
        if not document_content.strip():
            return "⚠️ No document content available."

        prompt = f"""
        You are a helpful AI assistant. You are given a document:

        ---
        {document_content}
        ---

        Based only on the information in this document, answer:
        {user_question}
        """

        try:
            return chat_response(prompt, self.model_choice)
        except Exception as e:
            print(f"AIService.get_response error: {e}")
            return f"Error: {e}"

    def get_tags_and_summary(self, document_content: str) -> (str, str):
        """
        Generate summary + tags. Uses Gemini first, Phi-2 if unavailable.
        """
        if not document_content.strip():
            return "", ""

        text = document_content[:8000]

        try:
            summary = summarize_doc(text)
        except Exception as e:
            print(f"Summarization failed: {e}")
            summary = ""

        tags = []
        if summary:
            for word in summary.split():
                if len(word) > 5 and word[0].isalpha():
                    tags.append(word.strip(".,").capitalize())
            tags = list(dict.fromkeys(tags))[:5]
        tags_str = ", ".join(tags)

        return tags_str, summary

    def get_file_category(self, file_name: str, file_content: str) -> str:
        """
        Retained for local auto-sorting – still uses old logic if Gemini available.
        """
        from pathlib import Path

        categories = [
            "Invoices", "Receipts", "Documents", "Contracts", "Resumes",
            "Code", "Scripts", "Logs", "Databases",
            "Images", "Videos", "Audio",
            "Archives", "Installers", "Temporary",
            "Notes", "Books", "Other"
        ]

        ext = Path(file_name).suffix.lower()

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

        return "Documents"
