import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

YOUR_API_KEY = os.environ.get("GOOGLE_API_KEY")


class AIService:
    def __init__(self):
        try:
            if not YOUR_API_KEY:
                raise ValueError("GOOGLE_API_KEY not found. Please check your .env file.")

            genai.configure(api_key=YOUR_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.chat = self.model.start_chat(history=[])
        except Exception as e:
            print(f"Error initializing AI Service: {e}")
            self.model = None

    def get_response(self, document_content: str, user_question: str) -> str:
        if not self.model:
            return "AI Service is not configured. Check your API key or .env file."

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
            return response.text
        except Exception as e:
            print(f"Error getting response from AI: {e}")
            return f"Error from AI: {e}"

    def get_tags_and_summary(self, document_content: str) -> (str, str):
        if not self.model:
            return "", ""

        truncated_content = document_content[:10000]

        prompt = f"""
        Analyze the document provided below.

        DOCUMENT:
        ---
        {truncated_content}
        ---

        Respond *only* in JSON format with two keys:
        1. "summary": A single-sentence summary of the document.
        2. "tags": A JSON array of 5-10 relevant keywords.

        JSON:
        """

        try:
            response = self.model.generate_content(prompt)

            clean_text = response.text.strip().replace("```json", "").replace("```", "")

            match = re.search(r'\{.*\}', clean_text, re.DOTALL)
            if not match:
                return "", ""

            data = json.loads(match.group(0))

            summary = data.get('summary', '')
            tags_list = data.get('tags', [])

            tags_str = ", ".join(tags_list)

            return tags_str, summary

        except Exception as e:
            print(f"Error getting AI tags/summary: {e}")
            return "", ""

    def get_file_category(self, file_name: str, file_content: str) -> str:
        if not self.model:
            return "Uncategorized"

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

        truncated_content = file_content[:2000]

        prompt = f"""
        You are a file organizer. Your job is to assign a single, one-word category
        to a file based on its name and content.

        Choose only from this list:
        {", ".join(categories)}

        FILE NAME:
        {file_name}

        FILE CONTENT (first 2000 characters):
        ---
        {truncated_content}
        ---

        Respond with ONLY the category name.
        CATEGORY:
        """

        try:
            response = self.model.generate_content(prompt)
            category = (response.text or "").strip().title()

            category = category.replace("Files", "").replace("File", "").strip()
            if category.endswith("s") and category[:-1] in categories:
                category = category[:-1]

            for c in categories:
                if category.lower() == c.lower() or category.lower().startswith(c.lower()):
                    return c

            return "Other"

        except Exception as e:
            print(f"Error getting AI category: {e}")
            return "Other"
