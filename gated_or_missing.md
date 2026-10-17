# Access: what you need to run each model

The harness reads API keys from environment variables only. Never commit a key.

| Backend (`--model`) | Env var | Model id | Notes |
|---|---|---|---|
| `nous` (used for all frontier results here) | `NOUS_API_KEY` | `--model-id`, e.g. `anthropic/claude-opus-5.5` | OpenAI-compatible endpoint `https://inference-api.nousresearch.com/v1`. `REASONING_EFFORT` (default `medium`) and `MAX_TOKENS` (default 12000) are read from env. |
| `grok` | `XAI_API_KEY` | `XAI_MODEL` | Direct xAI API, https://console.x.ai |
| `gpt` | `OPENAI_API_KEY` | `OPENAI_MODEL` | Direct OpenAI API |
| `claude` | `ANTHROPIC_API_KEY` | `ANTHROPIC_MODEL` | Direct Anthropic Messages API |
| `gemini` | `GEMINI_API_KEY` | `GEMINI_MODEL` | Direct Google AI Studio API |
| `local` | none | `--model-id` label, `LOCAL_BASE` server URL | Any OpenAI-compatible local server (llama.cpp, Ollama). See `run_local.sh`. |

The LLM grader (`labs_eval/judge.py`) also uses `NOUS_API_KEY`.

## Cost per model (130 cases, from the API's reported usage.cost)
| Model | Cost (USD) |
|---|---|
| anthropic/claude-opus-5.5 | 1.77 |
| openai/gpt-6-astra | 2.35 |
| x-ai/grok-4.7 | 1.07 |
| google/gemini-4-argon | 0.49 |
| deepseek/deepseek-v4-pro-0813 | 0.48 |
| openai/gpt-6.1-sol | 0.45 |

LLM grading cost about $0.02-0.03 per model. Prices change; check current pricing before running.

## Gated or not used
- **MedGemma** (Google's medical open model) is gated on Hugging Face behind a license click-through and was not run.
- **Larger open-weight models** (for example Qwen3.6-35B-A3B, gpt-oss-20b) need a GPU to run in reasonable time and are not in v1.
  An incomplete 26-case preview of Qwen3.6-35B-A3B exists but is excluded from results.
- **ABIM reference-range PDF** was downloadable without login. It is copyrighted, so it stays local and git-ignored.
