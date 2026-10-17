#!/bin/bash
# Sequential CPU runs of small open models through a llama.cpp server (resumable).
# LLAMA_DIR: directory with the llama-server binary. MODELS_DIR: directory with the GGUF files.
set -e
cd "$(dirname "$0")"
LLAMA_DIR="${LLAMA_DIR:-$HOME/llama.cpp}"
MODELS_DIR="${MODELS_DIR:-$HOME/models}"
THREADS="${THREADS:-6}"
mkdir -p results
run() { # $1 gguf file name, $2 label
  pkill -f llama-server || true; sleep 2
  (cd "$LLAMA_DIR" && ./llama-server -m "$MODELS_DIR/$1" -c 4096 -t "$THREADS" -np 1 --port 8080 > /dev/null 2>&1 &)
  until curl -s localhost:8080/health | grep -q ok; do sleep 3; done
  MAX_TOKENS=700 python3 labs_eval/run_models.py --model local --model-id "$2" --label "$2" >> "results/run_$2.log" 2>&1
}
run Qwen2.5-1.5B-Instruct-Q4_K_M.gguf qwen2.5-1.5b-instruct-q4km
run Llama-3.2-3B-Instruct-Q4_K_M.gguf llama3.2-3b-instruct-q4km
pkill -f llama-server || true
