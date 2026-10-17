#!/bin/bash
# Full 130-case frontier runs via the Nous Portal (needs NOUS_API_KEY in the environment).
# Resumable: run_models.py skips ids already in the raw jsonl.
cd "$(dirname "$0")"
: "${NOUS_API_KEY:?set NOUS_API_KEY}"
mkdir -p results
for m in anthropic/claude-opus-5.5 google/gemini-4-argon openai/gpt-6.1-sol openai/gpt-6-astra x-ai/grok-4.7 deepseek/deepseek-v4-pro-0813; do
  lab=$(echo "$m" | cut -d/ -f2)
  REASONING_EFFORT=medium python3 labs_eval/run_models.py --model nous --model-id "$m" --label "$lab" > "results/run_$lab.log" 2>&1 &
done
wait
python3 labs_eval/score.py
for lab in claude-opus-5.5 gemini-4-argon gpt-6.1-sol gpt-6-astra grok-4.7 deepseek-v4-pro-0813; do
  python3 labs_eval/judge.py --label "$lab"
done
python3 labs_eval/score.py && python3 labs_eval/report.py
