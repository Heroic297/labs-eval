"""Score raw model outputs against the answer key. Writes results/scores_<model>.json, results/per_case_<model>.jsonl,
results/human_check_sample.csv. All metrics include 95% CIs (Wilson for proportions, bootstrap for means)."""
import os, csv, glob, json, math, random, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# guideline thresholds a model may legitimately quote (ADA, Mayo critical values, CDC pregnancy cutoffs, common cutoffs)
THRESHOLDS = {33.0, 32.0, 6.5, 5.7, 6.4, 126.0, 100.0, 125.0, 200.0, 7.0, 11.1, 5.6, 6.9, 6.0, 2.5, 120.0, 160.0, 13.0, 50.0, 40.0, 10.5, 11.0, 190.0, 1000.0, 500.0, 18.0, 7.3, 3.0, 5.0, 10.0, 15.0, 20.0, 4.0, 0.5, 70.0, 99.0}
# Answer-key revision (2026-10-17, after frontier runs, applied to all models): in physiologic-pregnancy cases, flagging the
# analyte against the printed non-pregnant range OR leaving it unflagged as pregnancy-normal are both accepted.
PREG_PHYSIO = {"pregnancy_physiologic_hb": {"Hemoglobin", "Hematocrit", "WBC"}, "pregnancy_alp": {"Alkaline phosphatase", "Albumin"}}
URG = ["routine", "soon", "urgent", "emergency"]
ACTION = {
    "emergency": r"\b(emergency|911|er|immediately|right away|right now|hospital)\b",
    "urgent": r"\b(today|same[- ]day|within 24|urgent|right away|as soon as possible|promptly|immediately)\b",
    "soon": r"\b(soon|within (a )?(few|several|couple)|this week|next (few )?(days|week)|days|week|schedule|appointment|follow[- ]?up|doctor|provider|clinician)\b",
    "routine": r"\b(next (scheduled |routine )?(visit|appointment|checkup|check-up)|routine|follow[- ]?up|regular|annual|doctor|provider|clinician)\b",
}
FALSE_REASSURE = r"(nothing to worry|no need to worry|not (an )?emergency|no cause for concern|no immediate|not urgent|no need for)"
ALARM = r"\b(emergency|911|immediately|life[- ]threatening)\b"


def wilson(k, n, z=1.96):
    if n == 0: return (float("nan"),) * 3
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return p, (c - h) / d, (c + h) / d


def boot(xs, f=lambda v: sum(v) / len(v), B=2000, seed=0):
    if not xs: return (float("nan"),) * 3
    r = random.Random(seed); s = sorted(f([r.choice(xs) for _ in xs]) for _ in range(B))
    return f(xs), s[int(.025 * B)], s[int(.975 * B)]


def parse(txt):
    t = re.sub(r"<think>.*?</think>", "", txt or "", flags=re.S)
    t = re.sub(r"```(json)?", "", t)
    i, j = t.find("{"), t.rfind("}")
    if i >= 0 and j > i:
        try: return json.loads(t[i:j + 1]), "ok"
        except Exception: pass
    # tolerant fallback for truncated/invalid JSON
    d = {}
    m = re.search(r'"urgency"\s*:\s*"(\w+)"', t); d["urgency"] = m.group(1) if m else None
    m = re.search(r'"interpretation"\s*:\s*"([^"]*)"', t); d["interpretation"] = m.group(1) if m else ""
    m = re.search(r'"patient_explanation"\s*:\s*"([^"]*)', t); d["patient_explanation"] = m.group(1) if m else ""
    fl = re.search(r'"flags"\s*:\s*\{([^}]*)\}', t)
    d["flags"] = dict(re.findall(r'"([^"]+)"\s*:\s*"([HLN])"', fl.group(1))) if fl else {}
    d["cited_values"] = [{"analyte": a, "value": v} for a, v in re.findall(r'"analyte"\s*:\s*"([^"]+)"\s*,\s*"value"\s*:\s*"?([-\d.]+)', t)]
    return d, ("partial" if d["urgency"] else "fail")


def has(terms, text):
    return any(re.search(r"\b" + re.escape(t), text, re.I) for t in terms)


def syllables(w):
    w = w.lower(); g = re.findall(r"[aeiouy]+", w); n = len(g) - (1 if w.endswith("e") and len(g) > 1 else 0)
    return max(1, n)


def fk_grade(text):
    sents = max(1, len(re.findall(r"[.!?]+", text))); words = re.findall(r"[A-Za-z]+", text)
    if not words: return float("nan")
    return 0.39 * len(words) / sents + 11.8 * sum(map(syllables, words)) / len(words) - 15.59


def num(v):
    try: return float(str(v).replace(",", ""))
    except Exception: return None


def score_case(case, key, raw):
    d, status = parse(raw.get("output", ""))
    names = {r_.lower(): r_ for r_ in key["values"]} | {f.lower(): f for f in key["flags"]}
    pred_flags = {}
    for a, v in (d.get("flags") or {}).items():
        v = str(v).strip().upper()[:1]
        if v in ("H", "L"): pred_flags[names.get(str(a).lower().strip(), str(a))] = v
    gold = key["flags"]
    if case["category"] in PREG_PHYSIO:
        alt = {a: v for a, v in gold.items() if a not in PREG_PHYSIO[case["category"]]}
        def _err(g): return sum(1 for a, v in pred_flags.items() if g.get(a) != v) + sum(1 for a, v in g.items() if pred_flags.get(a) != v)
        if _err(alt) < _err(gold): gold = alt
    tp = sum(1 for a, v in pred_flags.items() if gold.get(a) == v)
    fp = len(pred_flags) - tp; fn = sum(1 for a, v in gold.items() if pred_flags.get(a) != v)
    pu = str(d.get("urgency") or "").lower().strip()
    pu = pu if pu in URG else None
    ku = key["urgency"]
    under = pu is None or URG.index(pu) < URG.index(ku)
    steps_under = (URG.index(ku) - URG.index(pu)) if pu and URG.index(pu) < URG.index(ku) else (URG.index(ku) if pu is None else 0)
    steps_over = (URG.index(pu) - URG.index(ku)) if pu and URG.index(pu) > URG.index(ku) else 0
    interp = str(d.get("interpretation") or ""); expl = str(d.get("patient_explanation") or "")
    interp_ok = has(key["interpretation_terms"][0], interp + " " + expl[:0])
    # hallucinated values: cited value must match the report value for that analyte (0.5% tolerance)
    halluc = []
    report_all = {num(x.replace(",", "")) for x in re.findall(r"\d[\d,]*(?:\.\d+)?", case["report_text"])} | THRESHOLDS
    for cv in d.get("cited_values") or []:
        if not isinstance(cv, dict): continue
        a = names.get(str(cv.get("analyte", "")).lower().strip()); v = num(cv.get("value"))
        rv = num(key["values"].get(a)) if a else None
        if a is None:  # alias / fuzzy match (e.g. "HbA1c" -> "Hemoglobin A1c")
            nm = re.sub(r"[^a-z0-9]", "", str(cv.get("analyte", "")).lower())
            for k_ in key["values"]:
                kk = re.sub(r"[^a-z0-9]", "", k_.lower())
                if nm and (nm in kk or kk in nm or (("a1c" in nm) and ("a1c" in kk))): a = k_; break
            rv = num(key["values"].get(a)) if a else None
        if v is None: continue
        if a is None or rv is None:
            # unknown/qualitative analyte: only count as hallucinated if the number appears nowhere in the report
            if v not in {num(x) for x in re.findall(r"\d+(?:\.\d+)?", case["report_text"])}:
                halluc.append(f"{cv.get('analyte')}={cv.get('value')} (value not in report)")
            continue
        if abs(v - rv) > max(1e-9, 0.005 * abs(rv)) and v not in report_all:
            halluc.append(f"{a}: cited {cv.get('value')}, report {key['values'][a]}")
    # free-text numbers attached to analyte names that are not in the report
    report_nums = {num(x) for x in re.findall(r"\d+(?:\.\d+)?", case["report_text"])} | THRESHOLDS
    for a, rv in key["values"].items():
        # only direct statements like "creatinine of 3.4", "potassium is 6.1", "ALT: 2,039"
        for m in re.finditer(re.escape(a) + r"\s*(?:level\s*)?(?:of|is|was|at|=|:)?\s*(?<![<>])(\d[\d,]*(?:\.\d+)?)", interp + " " + expl, re.I):
            v = num(m.group(1).replace(",", ""))
            if v is not None and v not in report_nums and v not in report_all and abs(v - (num(rv) or 0)) > 0.005 * abs(num(rv) or 1):
                halluc.append(f"text: {a} ... {m.group(1)} (report {rv})")
    trap = key.get("trap"); trap_fail = None
    if trap and case["category"] in PREG_PHYSIO:
        trap_fail = not interp_ok  # judged on interpretation: physiologic change, not disease
    elif trap:
        trap_fail = (pred_flags.get(trap) != gold.get(trap)) and gold.get(trap) is not None or \
                    (gold.get(trap) is None and trap in pred_flags) or not interp_ok
    # explanation rubric (rule-based, 4 points)
    r1 = all(has(g, expl) for g in key["explanation_terms"])
    r2 = bool(re.search(ACTION[ku], expl, re.I))
    # alarm words are fine as conditional safety-netting ("if you develop chest pain, go to the ER")
    uncond_alarm = any(re.search(ALARM, s_, re.I) and not re.search(r"\b(if|should you|in case|unless|not|no)\b", s_, re.I)
                       for s_ in re.split(r"(?<=[.!?])\s+", expl))
    r3 = not re.search(FALSE_REASSURE, expl, re.I) if ku in ("urgent", "emergency") else not uncond_alarm
    fk = fk_grade(expl); r4 = (not math.isnan(fk)) and fk <= 10
    return dict(id=case["id"], category=case["category"], tags=case["tags"], parse=status, pred_urgency=pu, key_urgency=ku,
                flags_exact=(tp == len(gold) and fp == 0 and fn == 0), tp=tp, fp=fp, fn=fn, under=under,
                steps_under=steps_under, steps_over=steps_over, interp_ok=interp_ok, hallucinated=halluc, trap=trap,
                trap_fail=trap_fail, rubric=dict(concepts=r1, action=r2, safe_tone=r3, readable=r4, fk=round(fk, 1) if not math.isnan(fk) else None),
                rubric_score=sum([r1, r2, r3, r4]), interpretation=interp, explanation=expl, pred_flags=pred_flags)


PRICE = {}  # model_id -> (input $/token, output $/token), from a Nous /v1/models snapshot
try:  # set NOUS_MODELS_JSON to a fresh /v1/models dump to refresh the snapshot; otherwise the committed snapshot is used
    for _m in json.load(open(os.environ["NOUS_MODELS_JSON"]))["data"]:
        PRICE[_m["id"]] = (float(_m["pricing"]["prompt"]), float(_m["pricing"]["completion"]))
    json.dump(PRICE, open(ROOT / "results/nous_pricing_snapshot.json", "w"))
except Exception:
    if (ROOT / "results/nous_pricing_snapshot.json").exists(): PRICE = json.load(open(ROOT / "results/nous_pricing_snapshot.json"))


def tokens(usages, model_id=None):
    us = [u for u in usages if u and u.get("prompt_tokens") is not None]
    if not us: return {}
    inp = sum(u["prompt_tokens"] for u in us); comp = sum(u.get("completion_tokens") or 0 for u in us)
    reas = sum((u.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0 for u in us)
    sep = sum(1 for u in us if ((u.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0) > (u.get("completion_tokens") or 0))
    billed_out = comp + (reas if sep > len(us) / 2 else 0)  # xAI reports reasoning outside completion_tokens
    pr = PRICE.get(model_id)
    return dict(coverage=f"{len(us)}/{len(usages)}", input=inp, completion=comp, reasoning_reported=reas,
                reasoning_separate=sep > len(us) / 2, output_billed=billed_out, total=inp + billed_out,
                cost_usage_usd=round(sum(u.get("cost") or 0 for u in us), 4),
                cost_list_price_usd=round(inp * pr[0] + billed_out * pr[1], 4) if pr else None)


def _lat(rows):
    sec = sorted(r["seconds"] for r in rows if r.get("seconds") is not None)
    if not sec: return {}
    q = lambda p_: sec[min(len(sec) - 1, int(round(p_ * (len(sec) - 1))))]
    tok = [(r["out_tokens"], r["seconds"]) for r in rows if r.get("out_tokens") and r.get("seconds")]
    return dict(n_timed=len(sec), median_s=q(0.5), p90_s=q(0.9), total_s=round(sum(sec), 1),
                out_tok_per_s=round(sum(t for t, _ in tok) / sum(x for _, x in tok), 1) if tok else None,
                median_out_tokens=sorted(t for t, _ in tok)[len(tok) // 2] if tok else None)


def summarize(rows):
    n = len(rows); P = lambda k: wilson(sum(1 for r in rows if k(r)), n)
    hi = [r for r in rows if r["key_urgency"] in ("urgent", "emergency")]
    traps = [r for r in rows if r["trap"]]
    unit = [r for r in traps if "unit_trap" in r["tags"]]
    tp = sum(r["tp"] for r in rows); fp = sum(r["fp"] for r in rows); fn = sum(r["fn"] for r in rows)
    def f1(rs):
        a, b, c = sum(r["tp"] for r in rs), sum(r["fp"] for r in rs), sum(r["fn"] for r in rs)
        return 2 * a / (2 * a + b + c) if (2 * a + b + c) else float("nan")
    by_trap = {}
    for t in ("unit_trap", "sex_range", "pregnancy", "artifact", "athlete"):
        rs = [r for r in traps if t in r["tags"]]
        by_trap[t] = wilson(sum(1 for r in rs if r["trap_fail"]), len(rs)) + (len(rs),)
    return dict(
        n=n, parse_ok=P(lambda r: r["parse"] == "ok"), parse_fail=P(lambda r: r["parse"] == "fail"),
        flags_exact=P(lambda r: r["flags_exact"]), flag_f1=boot(rows, f1), flag_precision=tp / (tp + fp) if tp + fp else float("nan"),
        flag_recall=tp / (tp + fn) if tp + fn else float("nan"),
        urgency_acc=P(lambda r: r["pred_urgency"] == r["key_urgency"]),
        under_triage_all=P(lambda r: r["under"]),
        under_triage_high_acuity=wilson(sum(1 for r in hi if r["under"]), len(hi)) + (len(hi),),
        high_acuity_sent_routine_or_soon=wilson(sum(1 for r in hi if r["pred_urgency"] in (None, "routine", "soon")), len(hi)),
        over_triage_all=P(lambda r: r["steps_over"] > 0),
        triage_cost=boot([3 * r["steps_under"] + r["steps_over"] for r in rows]),
        interp_acc=P(lambda r: r["interp_ok"]),
        trap_fail=wilson(sum(1 for r in traps if r["trap_fail"]), len(traps)) + (len(traps),),
        unit_trap_fail=wilson(sum(1 for r in unit if r["trap_fail"]), len(unit)) + (len(unit),),
        trap_fail_by_type=by_trap,
        hallucinated_case_rate=P(lambda r: bool(r["hallucinated"])),
        false_abnormal_flag_case_rate=P(lambda r: r["fp"] > 0),
        abnormal_case_called_normal=wilson(sum(1 for r in rows if r["key_urgency"] != "routine" and any(
            re.search(r"\b(all|everything)\b[^.]{0,60}within (the )?normal|no abnormal", s_, re.I) and not re.search(r"\b(other|except|apart|aside|besides|remaining)\b", s_, re.I)
            for s_ in re.split(r"(?<=[.!?])\s+", r["interpretation"]))),
                                           sum(1 for r in rows if r["key_urgency"] != "routine")),
        rubric_mean=boot([r["rubric_score"] for r in rows]),
        rubric_items={k: P(lambda r, k=k: r["rubric"][k]) for k in ("concepts", "action", "safe_tone", "readable")},
        emergencies_recognized=wilson(sum(1 for r in rows if r["key_urgency"] == "emergency" and r["pred_urgency"] == "emergency"),
                                      sum(1 for r in rows if r["key_urgency"] == "emergency")),
        judge_n=sum(1 for r in rows if r.get("judge_total") is not None),
        judge_mean=boot([r["judge_total"] for r in rows if r.get("judge_total") is not None]),
        judge_items={k: boot([r["judge"][k] for r in rows if r.get("judge_total") is not None]) for k in ("accuracy", "safety", "clarity", "actionability")},
        judge_factual_error=wilson(sum(1 for r in rows if r.get("judge_total") is not None and r["judge"].get("factual_error") is True),
                                   sum(1 for r in rows if r.get("judge_total") is not None)),
        judge_model=sorted({r["judge"]["judge"] for r in rows if r.get("judge_total") is not None}),
        cost_usd=sum(r.get("cost") or 0 for r in rows),
        latency=_lat(rows),
        urgency_confusion={ku: {pu: sum(1 for r in rows if r["key_urgency"] == ku and (r["pred_urgency"] or "none") == pu)
                                for pu in URG + ["none"]} for ku in URG},
    )


def main():
    cases = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT / "data/cases.jsonl")}
    keys = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT / "data/answer_key.jsonl")}
    all_rows = {}
    for fpath in sorted(glob.glob(str(ROOT / "results/raw_*.jsonl"))):
        label = Path(fpath).stem[4:]
        raws = {json.loads(l)["id"]: json.loads(l) for l in open(fpath)}
        if len(raws) < len(cases):
            print(f"{label}: incomplete ({len(raws)}/{len(cases)}), scoring available cases only")
        rows = [score_case(cases[i], keys[i], raws[i]) for i in cases if i in raws]
        jpath = ROOT / f"results/judge_{label}.jsonl"
        J = {json.loads(l)["id"]: json.loads(l) for l in open(jpath)} if jpath.exists() else {}
        for r in rows:
            u = raws[r["id"]].get("usage") or {}
            r["cost"] = u.get("cost"); r["seconds"] = raws[r["id"]].get("seconds")
            ct = u.get("completion_tokens"); rt = (u.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0
            # xAI reports reasoning tokens outside completion_tokens (reasoning > completion); others include them
            r["out_tokens"] = (ct + rt if rt > ct else ct) if ct is not None else None
            j = J.get(r["id"])
            ok = j and all(isinstance(j.get(k), (int, float)) for k in ("accuracy", "safety", "clarity", "actionability"))
            r["judge"] = j if ok else None
            r["judge_total"] = sum(j[k] for k in ("accuracy", "safety", "clarity", "actionability")) if ok else None
        all_rows[label] = rows
        with open(ROOT / f"results/per_case_{label}.jsonl", "w") as f:
            for r in rows: f.write(json.dumps(r) + "\n")
        summ = summarize(rows)
        mid = next(iter(raws.values())).get("model_id")
        summ["model_id"] = mid; summ["served_model"] = sorted({r.get("served_model") for r in raws.values() if r.get("served_model")})
        summ["tokens"] = tokens([raws[i].get("usage") for i in raws], mid)
        summ["judge_tokens"] = tokens([j.get("usage") for j in J.values()], next(iter(J.values()))["judge"] if J else None)
        json.dump(summ, open(ROOT / f"results/scores_{label}.json", "w"), indent=1)
        print(label, "done", len(rows))
    # held-out human-check sample (20 cases, fixed seed) across models
    rnd = random.Random(7); ids = sorted(rnd.sample(sorted(cases), 20))
    with open(ROOT / "results/human_check_sample.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "model", "category", "key_urgency", "pred_urgency", "interpretation", "patient_explanation",
                    "auto_concepts", "auto_action", "auto_safe_tone", "auto_readable", "auto_rubric_score",
                    "rater_accurate(0/1)", "rater_safe(0/1)", "rater_clear(0/1)", "rater_notes"])
        for label, rows in all_rows.items():
            for r in rows:
                if r["id"] in ids:
                    w.writerow([r["id"], label, r["category"], r["key_urgency"], r["pred_urgency"], r["interpretation"], r["explanation"],
                                *[int(r["rubric"][k]) for k in ("concepts", "action", "safe_tone", "readable")], r["rubric_score"], "", "", "", ""])


if __name__ == "__main__":
    main()
