#!/bin/bash
# 3-case smoke test per model before a full run (needs NOUS_API_KEY). Check results/smoke/ for cost per case.
cd "$(dirname "$0")"
: "${NOUS_API_KEY:?set NOUS_API_KEY}"
mkdir -p results/smoke
for m in anthropic/claude-opus-5.5 google/gemini-4-argon openai/gpt-6.1-sol openai/gpt-6-astra x-ai/grok-4.7 deepseek/deepseek-v4-pro-0813 deepseek/deepseek-v4.1-flash-1017; do
  lab=$(echo "$m" | tr '/' '_')
  REASONING_EFFORT=medium python3 labs_eval/run_models.py --model nous --model-id "$m" --label "smoke_$lab" --ids c039,c087,c104 > "results/smoke/$lab.log" 2>&1 &
done
wait
mv results/raw_smoke_*.jsonl results/smoke/ 2>/dev/null || true
