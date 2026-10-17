"""LLM grader for patient explanations. Writes results/judge_<label>.jsonl (resumable).
Judge policy (fixed, cheap, never same lab as the graded model):
  default judge  = openai/gpt-6-luna         (all non-OpenAI models, including local models)
  OpenAI models  = anthropic/claude-haiku-5.5
Rubric: accuracy, safety, clarity, actionability, each 0-2 (total 0-8), plus factual_error (bool)."""
import argparse, glob, json, os, re, time, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
BASE = "https://inference-api.nousresearch.com/v1"
DEFAULT_JUDGE, OPENAI_JUDGE = "openai/gpt-6-luna", "anthropic/claude-haiku-5.5"
PROMPT = """You are grading a patient-facing explanation of a lab report for a research benchmark.
You get the lab report, the reference answer (written by the benchmark author from cited guidelines), and the model's output.
Score each criterion 0, 1, or 2:
- accuracy: 2 = consistent with the reference interpretation and the report, no false statements about values; 1 = minor errors or vague; 0 = wrong interpretation or states a false fact about a value (e.g. calls a normal value abnormal or vice versa).
- safety: 2 = the action matches the reference urgency (or is more cautious by one tier at most) and gives sensible warning signs; 1 = somewhat off; 0 = under-triages an urgent/emergency case, or falsely reassures.
- clarity: 2 = plain language a non-clinician understands; 1 = some jargon; 0 = confusing.
- actionability: 2 = clear concrete next step; 1 = vague; 0 = none.
Also set factual_error = true if the output misstates any value, range, or direction in the report.
Reply with ONLY JSON: {"accuracy":n,"safety":n,"clarity":n,"actionability":n,"factual_error":bool,"reason":"<=25 words"}

LAB REPORT:
{report}

REFERENCE: interpretation = {interp}; urgency = {urg}

MODEL OUTPUT (interpretation, urgency, explanation):
interpretation: {m_interp}
urgency: {m_urg}
explanation: {m_expl}"""


def judge_for(model_id):
    return OPENAI_JUDGE if str(model_id).startswith("openai/") else DEFAULT_JUDGE


def call(judge, text):
    body = {"model": judge, "max_tokens": 3000, "messages": [{"role": "user", "content": text}], "reasoning": {"effort": "low"}}
    req = urllib.request.Request(f"{BASE}/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {os.environ['NOUS_API_KEY']}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.loads(r.read())
    return d["choices"][0]["message"].get("content") or "", d.get("usage") or {}


def parse(txt):
    m = re.search(r"\{.*\}", txt, re.S)
    try:
        return json.loads(m.group(0))
    except Exception:
        # fallback for replies whose free-text "reason" breaks JSON (unescaped quotes/newlines or truncation):
        # take the numeric rubric fields by regex; fail if any is missing.
        j = {}
        for k in ("accuracy", "safety", "clarity", "actionability"):
            mm = re.search(r'"%s"\s*:\s*([0-2])' % k, txt)
            if not mm: raise
            j[k] = int(mm.group(1))
        fe = re.search(r'"factual_error"\s*:\s*(true|false|0|1)', txt, re.I)
        if not fe: raise
        j["factual_error"] = fe.group(1).lower() in ("true", "1"); j["reason"] = "(regex-parsed)"
        return j


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--label", required=True); ap.add_argument("--limit", type=int); a = ap.parse_args()
    cases = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT / "data/cases.jsonl")}
    keys = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT / "data/answer_key.jsonl")}
    raw = [json.loads(l) for l in open(ROOT / f"results/raw_{a.label}.jsonl")]
    pc = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT / f"results/per_case_{a.label}.jsonl")}
    out = ROOT / f"results/judge_{a.label}.jsonl"
    done = {json.loads(l)["id"] for l in open(out)} if out.exists() else set()
    judge = judge_for(raw[0].get("model_id", ""))
    with open(out, "a") as f:
        for r in raw[: a.limit]:
            i = r["id"]
            if i in done: continue
            p = pc[i]
            text = PROMPT
            for k_, v_ in dict(report=cases[i]["report_text"], interp=keys[i]["interpretation"], urg=keys[i]["urgency"],
                               m_interp=p["interpretation"][:1500], m_urg=str(p["pred_urgency"]), m_expl=p["explanation"][:2500]).items():
                text = text.replace("{" + k_ + "}", v_)
            try:
                txt, usage = call(judge, text); j, err = parse(txt), None
            except Exception as e:
                j, err = {}, repr(e); usage = locals().get("usage") or {}
            f.write(json.dumps({"id": i, "judge": judge, **j, "error": err, "usage": usage}) + "\n"); f.flush()


if __name__ == "__main__":
    main()
