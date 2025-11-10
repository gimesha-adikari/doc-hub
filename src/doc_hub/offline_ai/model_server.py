from fastapi import FastAPI
from pydantic import BaseModel
from llama_cpp import Llama
import uvicorn
import os

MODEL_PATH = os.environ.get("LLM_MODEL_PATH")
MODEL_NAME = os.path.basename(MODEL_PATH) if MODEL_PATH else "unknown-model"

if not MODEL_PATH or not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("Model file not found. Set LLM_MODEL_PATH to a valid .gguf file.")

app = FastAPI(title=f"Offline AI Server - {MODEL_NAME}")

llm = Llama(model_path=MODEL_PATH, n_threads=8, n_ctx=2048)

class Prompt(BaseModel):
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.7

@app.post("/generate")
def generate(req: Prompt):
    result = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": "You are DocHub's offline AI assistant."},
            {"role": "user", "content": req.prompt},
        ],
        max_tokens=req.max_tokens,
        temperature=req.temperature,
    )
    return {"text": result["choices"][0]["message"]["content"]}

if __name__ == "__main__":
    port = int(os.environ.get("LLM_PORT", "7860"))
    uvicorn.run("model_server:app", host="127.0.0.1", port=port)
