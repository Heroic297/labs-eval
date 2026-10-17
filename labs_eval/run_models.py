"""Run lab-report cases through models. Backends: OpenAI-compatible (xAI, OpenAI, local llama.cpp server),
Anthropic Messages API, Google Gemini. Keys come from env vars only. Outputs results/raw_<model>.jsonl."""
import argparse, json, os, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SYSTEM = ("You are helping a patient understand a lab report. This is an evaluation of reading accuracy, not medical care. "
          "Respond with ONLY a JSON object, no markdown, with keys:\n"
          '"flags": object mapping each ABNORMAL analyte name (exactly as written in the report) to "H" or "L"; omit normal analytes. '
          "Judge against the reference range that applies to this patient.\n"
          '"interpretation": one or two sentences, the most likely overall interpretation.\n'
          '"urgency": one of "routine" (discuss at next scheduled visit), "soon" (see a clinician within days to 2 weeks), '
          '"urgent" (same day / within 24 hours), "emergency" (go to the emergency department or call 911 now).\n'
          '"cited_values": list of up to 5 {"analyte": name, "value": number exactly as shown in the report} for the key values your interpretation relies on.\n'
          '"patient_explanation": 3-6 plain-language sentences for the patient, including what to do next.')

MODELS = {  # name: (backend, model id, env key, base url)
    "grok": ("openai", os.getenv("XAI_MODEL", "grok-4"), "XAI_API_KEY", "https://api.x.ai/v1"),
    "gpt": ("openai", os.getenv("OPENAI_MODEL", "gpt-5"), "OPENAI_API_KEY", "https://api.openai.com/v1"),
    "claude": ("anthropic", os.getenv("ANTHROPIC_MODEL", "claude-opus-4-1"), "ANTHROPIC_API_KEY", "https://api.anthropic.com/v1"),
    "gemini": ("google", os.getenv("GEMINI_MODEL", "gemini-2.5-pro"), "GEMINI_API_KEY", "https://generativelanguage.googleapis.com/v1beta"),
    "nous": ("nous", None, "NOUS_API_KEY", "https://inference-api.nousresearch.com/v1"),
    "local": ("openai", os.getenv("LOCAL_MODEL", "local"), None, os.getenv("LOCAL_BASE", "http://127.0.0.1:8080/v1")),
}


def post(url, body, headers, timeout=600):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


LAST = {}


def call(backend, model, key, base, user):
    if backend == "nous":  # OpenAI-compatible; reasoning models: no temperature, fixed effort, generous token cap
        body = {"model": model, "max_tokens": int(os.getenv("MAX_TOKENS", "12000")),
                "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]}
        eff = os.getenv("REASONING_EFFORT", "medium")
        if eff != "default": body["reasoning"] = {"effort": eff}
        r = post(f"{base}/chat/completions", body, {"Authorization": f"Bearer {key}"})
        LAST.clear(); LAST.update(usage=r.get("usage"), served_model=r.get("model"), provider=r.get("provider"))
        return r["choices"][0]["message"].get("content") or ""
    if backend == "openai":
        h = {"Authorization": f"Bearer {key}"} if key else {}
        r = post(f"{base}/chat/completions", {"model": model, "temperature": 0, "max_tokens": int(os.getenv("MAX_TOKENS", "900")),
                 "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]}, h)
        return r["choices"][0]["message"].get("content") or ""
    if backend == "anthropic":
        r = post(f"{base}/messages", {"model": model, "max_tokens": 900, "temperature": 0, "system": SYSTEM,
                 "messages": [{"role": "user", "content": user}]}, {"x-api-key": key, "anthropic-version": "2023-06-01"})
        return "".join(b.get("text", "") for b in r["content"])
    if backend == "google":
        r = post(f"{base}/models/{model}:generateContent?key={key}", {"systemInstruction": {"parts": [{"text": SYSTEM}]},
                 "contents": [{"role": "user", "parts": [{"text": user}]}], "generationConfig": {"temperature": 0}}, {})
        return r["candidates"][0]["content"]["parts"][0]["text"]
    raise ValueError(backend)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=MODELS)
    ap.add_argument("--label", help="name for output file (default = model)")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--ids", help="comma-separated case ids to run (smoke tests)")
    ap.add_argument("--model-id", help="override model id (e.g. an Ollama tag)")
    a = ap.parse_args()
    backend, mid, envk, base = MODELS[a.model]
    mid = a.model_id or mid
    key = os.getenv(envk) if envk else None
    if envk and not key:
        sys.exit(f"missing {envk}; see gated_or_missing.md")
    label = a.label or a.model
    out = ROOT / "results" / f"raw_{label}.jsonl"
    done = set()
    if out.exists():
        done = {json.loads(l)["id"] for l in open(out)}
    cases = [json.loads(l) for l in open(ROOT / "data" / "cases.jsonl")][: a.limit]
    if a.ids: cases = [c for c in cases if c["id"] in a.ids.split(",")]
    with open(out, "a") as f:
        for c in cases:
            if c["id"] in done: continue
            t = time.time()
            try:
                txt, err = call(backend, mid, key, base, "Lab report:\n" + c["report_text"]), None
            except Exception as e:
                txt, err = "", repr(e)
            f.write(json.dumps({"id": c["id"], "model": label, "model_id": mid, "output": txt, "error": err,
                                "seconds": round(time.time() - t, 1), **LAST}) + "\n"); f.flush()
            LAST.clear()
            print(c["id"], round(time.time() - t, 1), "ERR" if err else "", flush=True)


if __name__ == "__main__":
    main()
