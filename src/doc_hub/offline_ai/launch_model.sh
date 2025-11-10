#!/bin/bash
source ~/venvs/llm/bin/activate

MODEL=$1

if [ "$MODEL" == "mistral" ]; then
    export LLM_MODEL_PATH="/home/gimesha/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    export LLM_PORT=7860
    echo "Starting Mistral model..."
elif [ "$MODEL" == "phi-2" ]; then
    export LLM_MODEL_PATH="/home/gimesha/models/phi-2.Q4_K_M.gguf"
    export LLM_PORT=7860
    echo "Starting Phi-2 model..."
else
    echo "Usage: ./launch_model.sh [mistral|phi-2]"
    exit 1
fi

python ~/My_Projects/Python/doc-hub/src/doc_hub/offline_ai/model_server.py
