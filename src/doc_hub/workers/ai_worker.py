from PySide6.QtCore import QObject, Signal, Slot

from src.doc_hub.core.ai_service import AIService

class AIWorker(QObject):

    response_ready = Signal(str,str)
    ai_error = Signal(str)

    def __init__(self, ai_service:AIService):
        super().__init__()
        self.ai_service = ai_service

    @Slot(str, str)
    def get_ai_response(self, document_content: str, user_question: str):
        try:
            answer = self.ai_service.get_response(document_content, user_question)

            if not answer or answer.lower().startswith("error") or "service is not" in answer.lower():
                self.ai_error.emit(answer)
            else:
                self.response_ready.emit(user_question, answer)

        except Exception as e:
            print(f"Error during background AI request: {e}")
            self.ai_error.emit(f"An unexpected error occurred: {e}")
