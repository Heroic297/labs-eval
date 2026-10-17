"""Build figures/ and results.md tables from results/scores_*.json and per_case_*.jsonl."""
import glob, json
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
URG = ["routine", "soon", "urgent", "emergency"]


def load():
    S, C = {}, {}
    for f in sorted(glob.glob(str(ROOT / "results/scores_*.json"))):
        m = Path(f).stem[7:]; S[m] = json.load(open(f))
        C[m] = [json.loads(l) for l in open(ROOT / f"results/per_case_{m}.jsonl")]
    return S, C


def pct(t):
    return f"{100*t[0]:.1f}% [{max(0, 100*t[1]):.1f}, {min(100, 100*t[2]):.1f}]"


def main():
    S, C = load(); models = list(S)
    (ROOT / "figures").mkdir(exist_ok=True)
    mets = [("urgency_acc", "Urgency exact"), ("under_triage_high_acuity", "Under-triage (urgent/emerg.)"),
            ("flags_exact", "Flags exact"), ("interp_acc", "Interpretation correct"), ("unit_trap_fail", "Unit-trap failure"),
            ("trap_fail", "Any-trap failure"), ("emergencies_recognized", "Emergencies recognized"), ("hallucinated_case_rate", "Hallucinated number (cases)"), ("false_abnormal_flag_case_rate", "Normal value flagged abnormal")]
    fig, ax = plt.subplots(figsize=(14, 5)); w = 0.8 / max(1, len(models)); x = np.arange(len(mets))
    for i, m in enumerate(models):
        v = [S[m][k][0] for k, _ in mets]; lo = [max(0, S[m][k][0] - S[m][k][1]) for k, _ in mets]; hi = [max(0, S[m][k][2] - S[m][k][0]) for k, _ in mets]
        ax.bar(x + i * w, v, w, yerr=[lo, hi], capsize=3, label=m)
    ax.set_xticks(x + w * (len(models) - 1) / 2); ax.set_xticklabels([n for _, n in mets], rotation=20, ha="right")
    ax.set_ylim(0, 1); ax.set_ylabel("rate (95% CI)"); ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=8); ax.set_title("Lab-report reading eval (130 synthetic cases)")
    fig.tight_layout(); fig.savefig(ROOT / "figures/headline_metrics.png", dpi=150); plt.close(fig)
    for m in models:
        cm = S[m]["urgency_confusion"]; cols = URG + ["none"]
        a = np.array([[cm[k][p] for p in cols] for k in URG])
        fig, ax = plt.subplots(figsize=(5.5, 4)); ax.imshow(a, cmap="Blues")
        for i in range(4):
            for j in range(5): ax.text(j, i, a[i, j], ha="center", va="center")
        ax.set_xticks(range(5)); ax.set_xticklabels(cols); ax.set_yticks(range(4)); ax.set_yticklabels(URG)
        ax.set_xlabel("model said"); ax.set_ylabel("answer key"); ax.set_title(f"Urgency confusion: {m}")
        fig.tight_layout(); fig.savefig(ROOT / f"figures/urgency_confusion_{m}.png", dpi=150); plt.close(fig)
    lat = [m for m in models if S[m].get("latency")]
    fig, ax = plt.subplots(figsize=(9, 4)); xs = np.arange(len(lat))
    ax.bar(xs - 0.2, [S[m]["latency"]["median_s"] for m in lat], 0.4, label="median")
    ax.bar(xs + 0.2, [S[m]["latency"]["p90_s"] for m in lat], 0.4, label="p90")
    ax.set_xticks(xs); ax.set_xticklabels(lat, rotation=20, ha="right"); ax.set_ylabel("seconds per case"); ax.legend()
    ax.set_title("Latency per case (API models: Nous Portal, 5 runs in parallel; local: CPU)")
    fig.tight_layout(); fig.savefig(ROOT / "figures/latency.png", dpi=150); plt.close(fig)
    tk = [m for m in models if S[m].get("tokens")]
    fig, ax1 = plt.subplots(figsize=(10, 4)); xs = np.arange(len(tk))
    inp = [S[m]["tokens"]["input"] / 1e3 for m in tk]; comp = [S[m]["tokens"]["completion"] / 1e3 for m in tk]
    extra = [(S[m]["tokens"]["output_billed"] - S[m]["tokens"]["completion"]) / 1e3 for m in tk]
    ax1.bar(xs, inp, 0.5, label="input"); ax1.bar(xs, comp, 0.5, bottom=inp, label="completion (incl. reasoning unless separate)")
    ax1.bar(xs, extra, 0.5, bottom=[a + b for a, b in zip(inp, comp)], label="reasoning billed separately (xAI)")
    ax1.set_ylabel("thousand tokens, 130 cases"); ax1.set_xticks(xs); ax1.set_xticklabels(tk, rotation=15, ha="right")
    ax2 = ax1.twinx(); ax2.plot(xs, [S[m]["tokens"]["cost_usage_usd"] for m in tk], "ko-", label="cost (USD)"); ax2.set_ylabel("USD")
    ax1.legend(loc="upper left", fontsize=8); ax2.legend(loc="upper right", fontsize=8); ax1.set_title("Tokens and cost per model (130 cases)")
    fig.tight_layout(); fig.savefig(ROOT / "figures/tokens_cost.png", dpi=150); plt.close(fig)
    types = ["unit_trap", "sex_range", "pregnancy", "artifact", "athlete"]
    fig, ax = plt.subplots(figsize=(8, 4)); x = np.arange(len(types))
    for i, m in enumerate(models):
        t = S[m]["trap_fail_by_type"]
        ax.bar(x + i * w, [t[k][0] for k in types], w, yerr=[[max(0, t[k][0] - t[k][1]) for k in types], [max(0, t[k][2] - t[k][0]) for k in types]], capsize=3, label=m)
    ax.set_xticks(x + w * (len(models) - 1) / 2); ax.set_xticklabels([f"{k}\n(n={S[models[0]]['trap_fail_by_type'][k][3]})" for k in types])
    ax.set_ylim(0, 1); ax.set_ylabel("failure rate (95% CI)"); ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=8); ax.set_title("Trap-case failure by type")
    fig.tight_layout(); fig.savefig(ROOT / "figures/trap_failures.png", dpi=150); plt.close(fig)
    # markdown tables
    L = ["| Metric | " + " | ".join(models) + " |", "|---|" + "---|" * len(models)]
    rows = [("Parsed as valid JSON", "parse_ok"), ("Urgency exact match", "urgency_acc"),
            ("Under-triage, all cases", "under_triage_all"), ("Under-triage, urgent/emergency cases", "under_triage_high_acuity"),
            ("Urgent/emergency case told routine or soon", "high_acuity_sent_routine_or_soon"), ("Over-triage, all cases", "over_triage_all"),
            ("Abnormal flags exactly right (case level)", "flags_exact"), ("Interpretation keyword match", "interp_acc"),
            ("Trap cases failed", "trap_fail"), ("Unit-trap cases failed", "unit_trap_fail"),
            ("Emergencies recognized (said emergency on emergency cases)", "emergencies_recognized"),
            ("Cases with a hallucinated value (number not in report)", "hallucinated_case_rate"),
            ("LLM judge: factual error in explanation", "judge_factual_error"),
            ("Cases with >=1 normal analyte flagged abnormal", "false_abnormal_flag_case_rate"),
            ("Non-routine case summarized as all normal", "abnormal_case_called_normal")]
    for name, k in rows: L.append(f"| {name} | " + " | ".join(pct(S[m][k]) for m in models) + " |")
    L.append("| Flag F1 (analyte level, bootstrap CI) | " + " | ".join(f"{S[m]['flag_f1'][0]:.2f} [{S[m]['flag_f1'][1]:.2f}, {S[m]['flag_f1'][2]:.2f}]" for m in models) + " |")
    L.append("| Triage cost (3x under-steps + over-steps, mean) | " + " | ".join(f"{S[m]['triage_cost'][0]:.2f} [{S[m]['triage_cost'][1]:.2f}, {S[m]['triage_cost'][2]:.2f}]" for m in models) + " |")
    L.append("| Explanation rubric (0-4, rule-based) | " + " | ".join(f"{S[m]['rubric_mean'][0]:.2f} [{S[m]['rubric_mean'][1]:.2f}, {S[m]['rubric_mean'][2]:.2f}]" for m in models) + " |")
    L.append("| LLM-judge explanation score (0-8, bootstrap CI) | " + " | ".join(f"{S[m]['judge_mean'][0]:.2f} [{S[m]['judge_mean'][1]:.2f}, {S[m]['judge_mean'][2]:.2f}]" for m in models) + " |")
    for k in ("accuracy", "safety", "clarity", "actionability"):
        L.append(f"| Judge: {k} (0-2) | " + " | ".join(f"{S[m]['judge_items'][k][0]:.2f}" for m in models) + " |")
    L.append("| Judge model | " + " | ".join(", ".join(S[m]['judge_model']) for m in models) + " |")
    L.append("| API cost for this run (USD, from usage.cost) | " + " | ".join(f"{S[m]['cost_usd']:.2f}" for m in models) + " |")
    for k, nm in (("median_s", "Latency median (s/case)"), ("p90_s", "Latency p90 (s/case)"), ("total_s", "Total wall time, 130 cases (s, sum of per-case)"), ("out_tok_per_s", "Output tokens/s"), ("median_out_tokens", "Median output tokens/case")):
        L.append(f"| {nm} | " + " | ".join(str(S[m].get('latency', {}).get(k, 'n/a')) for m in models) + " |")
    for k, nm in (("coverage", "Token usage coverage"), ("input", "Input tokens (total)"), ("completion", "Completion tokens (total)"),
                  ("reasoning_reported", "Reasoning tokens reported"), ("output_billed", "Output tokens billed (incl. reasoning)"),
                  ("total", "Total tokens"), ("cost_usage_usd", "Cost, from API usage.cost (USD)"), ("cost_list_price_usd", "Cost, list price x tokens (USD)")):
        L.append(f"| {nm} | " + " | ".join(str(S[m].get('tokens', {}).get(k, 'n/a')) for m in models) + " |")
    for k, nm in (("total", "Judge tokens (total)"), ("cost_usage_usd", "Judge cost (USD)")):
        L.append(f"| {nm} | " + " | ".join(str(S[m].get('judge_tokens', {}).get(k, 'n/a')) for m in models) + " |")
    for k in ("concepts", "action", "safe_tone", "readable"):
        L.append(f"| Rubric: {k} | " + " | ".join(pct(S[m]['rubric_items'][k]) for m in models) + " |")
    T = ["| Trap type | n | " + " | ".join(models) + " |", "|---|---|" + "---|" * len(models)]
    for t in types:
        T.append(f"| {t} | {S[models[0]]['trap_fail_by_type'][t][3]} | " + " | ".join(pct(S[m]['trap_fail_by_type'][t]) for m in models) + " |")
    open(ROOT / "results/tables.md", "w").write("\n".join(L) + "\n\n" + "\n".join(T) + "\n")
    print("\n".join(L)); print(); print("\n".join(T))


if __name__ == "__main__":
    main()
