from fastapi import FastAPI
from pydantic import BaseModel
from llama_cpp import Llama
import uvicorn, os

MODEL_PATH = os.environ.get(
    "LLM_MODEL_PATH",
    "/home/gimesha/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
)

llm = Llama(model_path=MODEL_PATH, n_threads=8, n_ctx=2048)
app = FastAPI(title="Local LLM API")

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
    text = result["choices"][0]["message"]["content"]
    return {"text": text}

if __name__ == "__main__":
    uvicorn.run("model_server:app", host="127.0.0.1", port=7860)
