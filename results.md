# Results: can AI models read a lab report?

Research benchmark, not medical advice. 130 synthetic cases (README, sources.md). Every number here comes from
`results/scores_*.json`, which `labs_eval/score.py` built from `results/raw_*.jsonl` and `results/judge_*.jsonl`. Brackets are 95% CIs
(Wilson for rates, 2,000-resample bootstrap for means).

**Runs (2026-10-17).** Frontier models ran through the Nous Portal (OpenAI-compatible) with the same system prompt, reasoning effort
`medium`, no temperature set (reasoning models), and one run each. Small open models ran locally on CPU with llama.cpp, Q4_K_M, temperature 0.
Model ids, all concrete (the `~latest` aliases were not used, and the served `model` field matched the requested id on every call):
`anthropic/claude-opus-5.5` (non-batch id exists and was used), `google/gemini-4-argon` (alias of gemini-4-argon-20261013),
`openai/gpt-6.1-sol` (alias of gpt-6.1-sol-20260929), `openai/gpt-6-astra` (alias of gpt-6-astra-20260903; non-batch, not -pro; added later the same day), `x-ai/grok-4.7` (the only Grok run), `deepseek/deepseek-v4-pro-0813`, `deepseek/deepseek-v4.1-flash-1017` (DeepSeek V4.1 Flash,
alias of deepseek-v4.1-flash-20261017, released 2026-10-17 and added the same day). The Nous model list shows low/high/max/none efforts for
V4.1 Flash, not medium; the `medium` request was accepted without error and is what was sent, as for every other model.

## Main table
| Model (id) | Urgency exact | Under-triage, urgent/emergency (n=42) | Emergencies recognized (n=35) | Unit-trap failure (n=13) | Flags exactly right | Hallucinated numbers | LLM-judge explanation (0-8) | Judge factual-error rate |
|---|---|---|---|---|---|---|---|---|
| claude-opus-5.5 (`anthropic/claude-opus-5.5`) | 98.5% [94.6, 99.6] | 0.0% [0.0, 8.4] | 35/35 100.0% [90.1, 100.0] | 0.0% [0.0, 22.8] | 99.2% [95.8, 99.9] | 0.0% [0.0, 2.9] | 7.91 [7.84, 7.96] | 2.3% [0.8, 6.6] |
| gemini-4-argon (`google/gemini-4-argon`) | 93.8% [88.3, 96.8] | 0.0% [0.0, 8.4] | 35/35 100.0% [90.1, 100.0] | 0.0% [0.0, 22.8] | 99.2% [95.8, 99.9] | 0.0% [0.0, 2.9] | 7.79 [7.70, 7.88] | 3.1% [1.2, 7.6] |
| grok-4.7 (`x-ai/grok-4.7`) | 91.5% [85.5, 95.2] | 0.0% [0.0, 8.4] | 35/35 100.0% [90.1, 100.0] | 0.0% [0.0, 22.8] | 99.2% [95.8, 99.9] | 0.0% [0.0, 2.9] | 7.95 [7.91, 7.98] | 1.5% [0.4, 5.4] |
| deepseek-v4-pro-0813 (`deepseek/deepseek-v4-pro-0813`) | 86.2% [79.2, 91.1] | 0.0% [0.0, 8.4] | 35/35 100.0% [90.1, 100.0] | 0.0% [0.0, 22.8] | 99.2% [95.8, 99.9] | 0.0% [0.0, 2.9] | 7.75 [7.65, 7.85] | 2.3% [0.8, 6.6] |
| gpt-6-astra (`openai/gpt-6-astra`) | 86.2% [79.2, 91.1] | 0.0% [0.0, 8.4] | 35/35 100.0% [90.1, 100.0] | 0.0% [0.0, 22.8] | 100.0% [97.1, 100.0] | 0.0% [0.0, 2.9] | 7.56 [7.44, 7.67] | 0.0% [0.0, 2.9] |
| gpt-6.1-sol (`openai/gpt-6.1-sol`) | 84.6% [77.4, 89.8] | 2.4% [0.4, 12.3] | 34/35 97.1% [85.5, 99.5] | 0.0% [0.0, 22.8] | 100.0% [97.1, 100.0] | 0.0% [0.0, 2.9] | 7.62 [7.52, 7.72] | 0.0% [0.0, 2.9] |
| deepseek-v4.1-flash-1017 (`deepseek/deepseek-v4.1-flash-1017`) | 84.6% [77.4, 89.8] | 2.4% [0.4, 12.3] | 34/35 97.1% [85.5, 99.5] | 0.0% [0.0, 22.8] | 97.7% [93.4, 99.2] | 0.0% [0.0, 2.9] | 7.78 [7.70, 7.85] | 2.3% [0.8, 6.6] |
| llama3.2-3b-instruct-q4km (`llama3.2-3b-instruct-q4km`) | 40.8% [32.7, 49.4] | 90.5% [77.9, 96.2] | 0/35 0.0% [0.0, 9.9] | 84.6% [57.8, 95.7] | 13.1% [8.3, 19.9] | 0.0% [0.0, 2.9] | 5.02 [4.76, 5.27] | 52.3% [43.8, 60.7] |
| qwen2.5-1.5b-instruct-q4km (`qwen2.5-1.5b-instruct-q4km`) | 23.1% [16.7, 31.0] | 90.5% [77.9, 96.2] | 0/35 0.0% [0.0, 9.9] | 92.3% [66.7, 98.6] | 0.0% [0.0, 2.9] | 0.0% [0.0, 2.9] | 4.42 [4.13, 4.70] | 76.9% [69.0, 83.3] |

## What the numbers say
1. **Frontier models nearly saturate this benchmark.** Six of seven got 0/47 trap cases wrong (CI upper bound 7.6%). DeepSeek V4.1 Flash
   missed 1 (c106, EDTA contamination: it treated K 9.2 as real and mentioned lab error only as something to "consider but not assume").
   All seven got 0/13 unit traps, and flags exactly right on 127 to 130 of 130. Opus 5.5 got urgency right on 128/130. The small models fail 75-77% of traps.
   v1 separates small from frontier models, but it is too easy to rank the frontier ones. v2 needs harder cases.
2. **Two frontier models each under-called one emergency, and none sent an urgent case to "routine" or "soon".**
   GPT-6.1 Sol on c088 (insulin user, glucose 2.3 mmol/L) said "urgent"; GPT-6 Astra said "emergency" on the same case: "get emergency
   medical help now and do not drive yourself". Sol's explanation still covers the right actions: "take 15-20 grams of fast-acting sugar ...
   If you become confused, faint, have a seizure, or cannot swallow" (then emergency care). DeepSeek V4.1 Flash on c087 (insulin user,
   glucose 2.2 mmol/L, sweaty and shaky) also said "urgent", with "take 15 grams of fast-acting sugar now". The other five recognized
   35/35 emergencies. Both small models never said "emergency" (0/35).
3. **Frontier differences are in over-triage and judgment calls**, not misses:
   - Lifter with post-squat CK and creatinine (key: routine recheck): 4 of 7 frontier models said "soon" on most of these cases
     (GPT-6.1 Sol 5/5, GPT-6 Astra 5/5, Grok 4/5, DeepSeek V4 Pro 4/5, DeepSeek V4.1 Flash 2/5, Opus 1/5, Gemini 0/5), but every one named exercise and creatine as the cause.
   - Triglycerides >1,000 (key: soon): GPT-6.1 Sol, GPT-6 Astra, Grok, DeepSeek V4 Pro and DeepSeek V4.1 Flash each said "urgent" on 3/3.
   - EDTA contamination (key: urgent redraw): GPT-6.1 Sol, GPT-6 Astra and DeepSeek V4.1 Flash said "emergency" on 3/3 and DeepSeek V4 Pro on 1/3. Sol's explanation: "if these results are
     real, they can cause dangerous heart rhythm problems even when you feel well. Go to the emergency department now". That is defensible.
   - Mild under-calls: Gemini said "routine" for 2 men with Hb 13.0 (key: soon) and 2 pseudothrombocytopenia cases. DeepSeek did the same
     on 2 + 2. Grok said "routine" for one hemolyzed K ("this does not look like a dangerous potassium problem").
   - GPT-6 Astra made the same over-calls as GPT-6.1 Sol: lifter 5/5 "soon", TG >1,000 3/3 "urgent", EDTA 3/3 "emergency",
     hemolyzed K 4 cases "urgent" (key: soon), mild asymptomatic hyponatremia 2 cases "soon" (key: routine). The two GPT models gave the
     same urgency tier on 126/130 cases. Astra's 18 misses: 17 too high and 1 too low (c075, a man with Hb slightly low, said "routine", key "soon").
   - DeepSeek V4.1 Flash has the most under-calls of any frontier model: 10 cases one tier too low (9 "soon" cases rated "routine":
     4 men with low Hb, 2 women with creatinine above the female range, 2 pseudothrombocytopenia, 1 hemolyzed K; plus the c087
     emergency) against 10 over-calls. It is also by far the cheapest: $0.05 for all 130 cases.
   - Triage cost (3 x under-steps + over-steps, lower is better): Opus 0.02, Grok 0.12, Gemini 0.14, GPT-6 Astra 0.15, GPT-6.1 Sol 0.20,
     DeepSeek V4 Pro 0.22, DeepSeek V4.1 Flash 0.31.
4. **No model invented a number.** All 9 models had 0/130 cases with a cited or stated value missing from the report. Wrong *claims*
   are a different story: the LLM judge flagged factual errors in 52.3% (Llama) and 76.9% (Qwen) of explanations, against 0-3.1% for frontier
   models. Llama on a normal panel: "Your white blood cell count is slightly higher than normal" (WBC 7.9, range 4.0-11.0).
5. **Readability is where frontier models lose rule-based points.** On Flesch-Kincaid grade <= 10: DeepSeek V4 Pro 90.0%, DeepSeek V4.1 Flash 60.8%, Grok 59.2%, Opus 55.4%,
   GPT-6.1 Sol 43.1%, GPT-6 Astra 38.5%, Gemini 16.2%. The judge rated clarity 2.00/2 for most of them anyway, so the two graders disagree here.

## Quoted failures
- Qwen2.5-1.5B, c087 (glucose 2.2 mmol/L, insulin, sweaty): "all electrolytes and metabolic parameters are within the normal range. There are no abnormal findings. No immediate action is needed."
- Llama-3.2-3B, c087: "The patient's low potassium level (4.1 mEq/L) is below the reference range (3.5-5.0 mEq/L)"
- Llama-3.2-3B, c047 (Na 117, confused): "please continue taking your medication as directed" (urgency "soon").
- Qwen2.5-1.5B, c104 (K 8.8, Ca 5.8, EDTA pattern): "The patient's results are all within the normal range".
- GPT-6.1 Sol, c088: urgency "urgent" on an emergency hypoglycemia case (quoted above). It's the only frontier under-triage.
- Grok 4.7, c044 (hemolyzed K): urgency "routine", "this does not look like a dangerous potassium problem" (key: soon, repeat draw).
- GPT-6 Astra, c075 (male, Hb slightly low, key soon): urgency "routine", "Discuss the results at your next scheduled visit". Its only under-call.
- GPT-6 Astra, c061 (lifter, key routine, said soon): "Your CK is substantially elevated, so it should not simply be dismissed even though you feel well".
- DeepSeek V4.1 Flash, c087 (glucose 2.2 mmol/L, insulin, sweaty): urgency "urgent" on an emergency case; "If you are still symptomatic, take 15 grams of fast-acting sugar now".
- DeepSeek V4.1 Flash, c106 (K 9.2, low Ca and ALP, well patient; key: EDTA contamination, urgent redraw): "Critical hyperkalemia ... pseudohyperkalemia or lab error should be considered but not assumed" (urgency "emergency"). Its only trap miss.
- DeepSeek V4.1 Flash, c044 (hemolyzed K): urgency "routine" (key: soon).
- Opus 5.5, c061 (lifter, key routine, said soon). The reasoning was right: "benign exercise-induced muscle enzyme release ... creatinine mildly raised by high muscle mass and creatine supplementation".

## Speed, tokens, cost
| Model | Median s/case | p90 s/case | Sum of per-case s (130) | Output tok/s | Input tok | Output tok billed (reasoning) | Total tok | Cost usage.cost | Cost list price | Judge tok / $ |
|---|---|---|---|---|---|---|---|---|---|---|
| claude-opus-5.5 | 6.3 | 8.4 | 840.5 | 88.0 | 72,556 | 73,990 (0) | 146,546 | $1.77 | $1.77 | 114,652 / $0.021 |
| gemini-4-argon | 6.6 | 8.5 | 921.1 | 40.0 | 59,353 | 36,851 (826) | 96,204 | $0.49 | $0.49 | 108,943 / $0.020 |
| grok-4.7 | 13.9 | 29.2 | 2296.6 | 63.8 | 212,582 | 147,047 (115,145, billed separately) | 359,629 | $1.07 | $1.31 | 105,002 / $0.018 |
| deepseek-v4-pro-0813 | 11.8 | 25.5 | 1799.7 | 65.2 | 50,780 | 117,350 (86,966) | 168,130 | $0.48 | $0.94 | 101,234 / $0.018 |
| gpt-6-astra | 5.5 | 7.9 | 762.6 | 48.0 | 52,055 | 36,601 (3,578) | 88,656 | $2.35 | $2.35 | 162,283 / $0.030 |
| gpt-6.1-sol | 6.6 | 9.3 | 902.4 | 38.6 | 52,055 | 34,808 (2,217) | 86,863 | $0.45 | $0.45 | 162,011 / $0.030 |
| deepseek-v4.1-flash-1017 | 12.9 | 34.1 | 2158.9 | 30.8 | 54,160 | 66,457 (38,338) | 120,617 | $0.050 | $0.039 | 102,744 / $0.018 |
| llama3.2-3b-instruct-q4km | 18.2 | 25.3 | 2517.4 | n/a | n/a | n/a | n/a | $0 (local CPU) | n/a | 102,571 / $0.020 |
| qwen2.5-1.5b-instruct-q4km | 13.8 | 24.7 | 2103.7 | n/a | n/a | n/a | n/a | $0 (local CPU) | n/a | 103,181 / $0.020 |

Latency notes: the first five frontier runs went 5 at a time in parallel over the Nous Portal, so latency includes portal routing and
queueing. GPT-6 Astra and DeepSeek V4.1 Flash ran later, each by itself (concurrency 1), so their latency is slightly flattered relative to the
parallel runs. During the Flash run the host paused several times, which inflates some per-case times (Flash p90 34.1 s). During the Astra run one request
(c042) hung with no reply for about 10 min; the run was stopped and resumed, and c042's time is from the retry. Opus 5.5 ran on the regular
id `anthropic/claude-opus-5.5`, not the `:batch` variant, so its latency is comparable to the others. The run host occasionally paused
processes, which can inflate single-case times, so p90 is less reliable than the median. Timing was logged per call for every case
(`seconds` in raw jsonl, 130/130 for all models). "Sum of per-case s" is the serial time; each model's run took about 15-40 min of
wall-clock. Token usage covers 130/130 for every API model. Small models ran locally with no token logging, so their tok/s is n/a. xAI
reports reasoning tokens outside `completion_tokens`, so "billed output" adds them back. Cost per model is the API's reported `usage.cost`
for the 130-case run; "list price" is tokens x the Nous Portal list price snapshot in `results/nous_pricing_snapshot.json`. DeepSeek's
reported cost ($0.48) is under list price x tokens ($0.94), probably from provider discounts. DeepSeek V4.1 Flash's reported cost ($0.049)
is above tokens x the snapshot list price of $0.10/$0.50 per M ($0.039), so the advertised discount did not show up in the reported cost. Figures: `figures/latency.png`,
`figures/tokens_cost.png`.

## Explanation grading
- **LLM judge** (`labs_eval/judge.py`): fixed cheap judges, never from the same lab as the model being graded. `openai/gpt-6-luna` graded
  every non-OpenAI model, including DeepSeek V4.1 Flash and the small models, and `anthropic/claude-haiku-5.5` graded both OpenAI models (GPT-6.1 Sol and GPT-6 Astra). Rubric: accuracy, safety,
  clarity, actionability, 0-2 each, plus a factual_error flag. Judge reasoning effort was low. Coverage is 130/130 for every model. Haiku sometimes
  broke JSON in its free-text reason field (3 Sol and 7 Astra replies). Those cases were re-judged with a parser that falls back to
  regex-reading the four 0-2 scores and the factual_error flag. 3 replies per GPT model needed that fallback. This moved Sol's judge
  mean from 7.61 (127 cases) to 7.62 (130).
- The judge is noisy. On Gemini c068 it claimed hematocrit was abnormal for a female when it was in range, and it docked Opus c111
  because "absence of clumps does not rule out every possible lab error". Use `results/human_check_sample.csv` (20 cases x 9 models)
  to see how well the judge matches a human.
- The rule-based rubric (0-4) is still in the full table for comparison.

## Answer-key revision (disclosed)
After the frontier runs I changed one scoring rule and applied it to every model. In physiologic-pregnancy cases (Hb drop at 29 weeks,
ALP/albumin at 34 weeks), the flags can now either follow the printed non-pregnant range or be left off as pregnancy-normal. The trap
is now judged on the interpretation. Frontier models applied pregnancy ranges and didn't flag these, which is clinically correct.
This moved Qwen2.5-1.5B's trap failure from 80.9% to 74.5% and its pregnancy failure from 100% to 50%. I also tightened the free-text
number check, because ratios like "BUN/creatinine ratio of about 24" and thresholds like ">2000" were counted as hallucinations before. No frontier
case changed from pass to fail.

When adding DeepSeek V4.1 Flash, the interpretation keyword for the two diabetes-range groups was widened from "diabetes" to the
prefix "diabet", because Flash wrote "in the diabetic range" (c084) and was marked as a trap failure. The cases are byte-identical;
re-scoring changed no other model's numbers. It moved Flash from 2/47 to 1/47 trap failures. Flash also flagged "Urine ketones 3+" from
the clinical note in 3 DKA cases; that row is not in the key, so those 3 cases count as not exactly right on flags.

## Full metric table
| Metric | claude-opus-5.5 | deepseek-v4-pro-0813 | deepseek-v4.1-flash-1017 | gemini-4-argon | gpt-6-astra | gpt-6.1-sol | grok-4.7 | llama3.2-3b-instruct-q4km | qwen2.5-1.5b-instruct-q4km |
|---|---|---|---|---|---|---|---|---|---|
| Parsed as valid JSON | 100.0% [97.1, 100.0] | 100.0% [97.1, 100.0] | 100.0% [97.1, 100.0] | 100.0% [97.1, 100.0] | 100.0% [97.1, 100.0] | 100.0% [97.1, 100.0] | 100.0% [97.1, 100.0] | 46.2% [37.8, 54.7] | 87.7% [80.9, 92.3] |
| Urgency exact match | 98.5% [94.6, 99.6] | 86.2% [79.2, 91.1] | 84.6% [77.4, 89.8] | 93.8% [88.3, 96.8] | 86.2% [79.2, 91.1] | 84.6% [77.4, 89.8] | 91.5% [85.5, 95.2] | 40.8% [32.7, 49.4] | 23.1% [16.7, 31.0] |
| Under-triage, all cases | 0.0% [0.0, 2.9] | 3.8% [1.7, 8.7] | 7.7% [4.2, 13.6] | 3.8% [1.7, 8.7] | 0.8% [0.1, 4.2] | 2.3% [0.8, 6.6] | 1.5% [0.4, 5.4] | 40.8% [32.7, 49.4] | 36.9% [29.1, 45.5] |
| Under-triage, urgent/emergency cases | 0.0% [0.0, 8.4] | 0.0% [0.0, 8.4] | 2.4% [0.4, 12.3] | 0.0% [0.0, 8.4] | 0.0% [0.0, 8.4] | 2.4% [0.4, 12.3] | 0.0% [0.0, 8.4] | 90.5% [77.9, 96.2] | 90.5% [77.9, 96.2] |
| Urgent/emergency case told routine or soon | 0.0% [0.0, 8.4] | 0.0% [0.0, 8.4] | 0.0% [0.0, 8.4] | 0.0% [0.0, 8.4] | 0.0% [0.0, 8.4] | 0.0% [0.0, 8.4] | 0.0% [0.0, 8.4] | 28.6% [17.2, 43.6] | 16.7% [8.3, 30.6] |
| Over-triage, all cases | 1.5% [0.4, 5.4] | 10.0% [5.9, 16.4] | 7.7% [4.2, 13.6] | 2.3% [0.8, 6.6] | 13.1% [8.3, 19.9] | 13.1% [8.3, 19.9] | 6.9% [3.7, 12.6] | 18.5% [12.7, 26.0] | 40.0% [32.0, 48.6] |
| Abnormal flags exactly right (case level) | 99.2% [95.8, 99.9] | 99.2% [95.8, 99.9] | 97.7% [93.4, 99.2] | 99.2% [95.8, 99.9] | 100.0% [97.1, 100.0] | 100.0% [97.1, 100.0] | 99.2% [95.8, 99.9] | 13.1% [8.3, 19.9] | 0.0% [0.0, 2.9] |
| Interpretation keyword match | 100.0% [97.1, 100.0] | 100.0% [97.1, 100.0] | 99.2% [95.8, 99.9] | 100.0% [97.1, 100.0] | 100.0% [97.1, 100.0] | 100.0% [97.1, 100.0] | 100.0% [97.1, 100.0] | 53.1% [44.5, 61.4] | 46.9% [38.6, 55.5] |
| Trap cases failed | 0.0% [0.0, 7.6] | 0.0% [0.0, 7.6] | 2.1% [0.4, 11.1] | 0.0% [0.0, 7.6] | 0.0% [0.0, 7.6] | 0.0% [0.0, 7.6] | 0.0% [0.0, 7.6] | 76.6% [62.8, 86.4] | 74.5% [60.5, 84.7] |
| Unit-trap cases failed | 0.0% [0.0, 22.8] | 0.0% [0.0, 22.8] | 0.0% [0.0, 22.8] | 0.0% [0.0, 22.8] | 0.0% [0.0, 22.8] | 0.0% [0.0, 22.8] | 0.0% [0.0, 22.8] | 84.6% [57.8, 95.7] | 92.3% [66.7, 98.6] |
| Emergencies recognized (said emergency on emergency cases) | 100.0% [90.1, 100.0] | 100.0% [90.1, 100.0] | 97.1% [85.5, 99.5] | 100.0% [90.1, 100.0] | 100.0% [90.1, 100.0] | 97.1% [85.5, 99.5] | 100.0% [90.1, 100.0] | 0.0% [0.0, 9.9] | 0.0% [0.0, 9.9] |
| Cases with a hallucinated value (number not in report) | 0.0% [0.0, 2.9] | 0.0% [0.0, 2.9] | 0.0% [0.0, 2.9] | 0.0% [0.0, 2.9] | 0.0% [0.0, 2.9] | 0.0% [0.0, 2.9] | 0.0% [0.0, 2.9] | 0.0% [0.0, 2.9] | 0.0% [0.0, 2.9] |
| LLM judge: factual error in explanation | 2.3% [0.8, 6.6] | 2.3% [0.8, 6.6] | 2.3% [0.8, 6.6] | 3.1% [1.2, 7.6] | 0.0% [0.0, 2.9] | 0.0% [0.0, 2.9] | 1.5% [0.4, 5.4] | 52.3% [43.8, 60.7] | 76.9% [69.0, 83.3] |
| Cases with >=1 normal analyte flagged abnormal | 0.8% [0.1, 4.2] | 0.8% [0.1, 4.2] | 2.3% [0.8, 6.6] | 0.8% [0.1, 4.2] | 0.0% [0.0, 2.9] | 0.0% [0.0, 2.9] | 0.8% [0.1, 4.2] | 75.4% [67.3, 82.0] | 99.2% [95.8, 99.9] |
| Non-routine case summarized as all normal | 0.0% [0.0, 4.1] | 0.0% [0.0, 4.1] | 0.0% [0.0, 4.1] | 1.1% [0.2, 6.0] | 0.0% [0.0, 4.1] | 0.0% [0.0, 4.1] | 0.0% [0.0, 4.1] | 0.0% [0.0, 4.1] | 10.0% [5.4, 17.9] |
| Flag F1 (analyte level, bootstrap CI) | 1.00 [0.99, 1.00] | 1.00 [0.99, 1.00] | 0.99 [0.99, 1.00] | 1.00 [0.99, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [0.99, 1.00] | 0.38 [0.32, 0.45] | 0.28 [0.22, 0.34] |
| Triage cost (3x under-steps + over-steps, mean) | 0.02 [0.00, 0.04] | 0.22 [0.12, 0.33] | 0.31 [0.18, 0.45] | 0.14 [0.05, 0.25] | 0.15 [0.08, 0.23] | 0.20 [0.11, 0.30] | 0.12 [0.05, 0.20] | 1.64 [1.34, 1.94] | 1.93 [1.64, 2.23] |
| Explanation rubric (0-4, rule-based) | 3.55 [3.46, 3.63] | 3.85 [3.78, 3.92] | 3.55 [3.46, 3.65] | 3.13 [3.06, 3.20] | 3.29 [3.19, 3.39] | 3.35 [3.25, 3.46] | 3.55 [3.46, 3.65] | 2.99 [2.86, 3.13] | 2.50 [2.32, 2.67] |
| LLM-judge explanation score (0-8, bootstrap CI) | 7.91 [7.84, 7.96] | 7.75 [7.65, 7.85] | 7.78 [7.70, 7.85] | 7.79 [7.70, 7.88] | 7.56 [7.44, 7.67] | 7.62 [7.52, 7.72] | 7.95 [7.91, 7.98] | 5.02 [4.76, 5.27] | 4.42 [4.13, 4.70] |
| Judge: accuracy (0-2) | 1.92 | 1.86 | 1.87 | 1.88 | 1.99 | 1.99 | 1.98 | 0.55 | 0.28 |
| Judge: safety (0-2) | 1.98 | 1.94 | 1.92 | 1.96 | 1.82 | 1.83 | 1.98 | 1.06 | 0.90 |
| Judge: clarity (0-2) | 2.00 | 2.00 | 2.00 | 2.00 | 1.77 | 1.81 | 2.00 | 1.98 | 1.82 |
| Judge: actionability (0-2) | 2.00 | 1.95 | 1.99 | 1.95 | 1.98 | 1.98 | 1.98 | 1.42 | 1.41 |
| Judge model | openai/gpt-6-luna | openai/gpt-6-luna | openai/gpt-6-luna | openai/gpt-6-luna | anthropic/claude-haiku-5.5 | anthropic/claude-haiku-5.5 | openai/gpt-6-luna | openai/gpt-6-luna | openai/gpt-6-luna |
| API cost for this run (USD, from usage.cost) | 1.77 | 0.48 | 0.05 | 0.49 | 2.35 | 0.45 | 1.07 | 0.00 | 0.00 |
| Latency median (s/case) | 6.3 | 11.8 | 12.9 | 6.6 | 5.5 | 6.6 | 13.9 | 18.2 | 13.8 |
| Latency p90 (s/case) | 8.4 | 25.5 | 34.1 | 8.5 | 7.9 | 9.3 | 29.2 | 25.3 | 24.7 |
| Total wall time, 130 cases (s, sum of per-case) | 840.5 | 1799.7 | 2158.9 | 921.1 | 762.6 | 902.4 | 2296.6 | 2517.4 | 2103.7 |
| Output tokens/s | 88.0 | 65.2 | 30.8 | 40.0 | 48.0 | 38.6 | 63.8 | None | None |
| Median output tokens/case | 546 | 737 | 445 | 269 | 250 | 242 | 909 | None | None |
| Token usage coverage | 130/130 | 130/130 | 130/130 | 130/130 | 130/130 | 130/130 | 130/130 | n/a | n/a |
| Input tokens (total) | 72556 | 50780 | 54160 | 59353 | 52055 | 52055 | 212582 | n/a | n/a |
| Completion tokens (total) | 73990 | 117350 | 66457 | 36851 | 36601 | 34808 | 31902 | n/a | n/a |
| Reasoning tokens reported | 0 | 86966 | 38338 | 826 | 3578 | 2217 | 115145 | n/a | n/a |
| Output tokens billed (incl. reasoning) | 73990 | 117350 | 66457 | 36851 | 36601 | 34808 | 147047 | n/a | n/a |
| Total tokens | 146546 | 168130 | 120617 | 96204 | 88656 | 86863 | 359629 | n/a | n/a |
| Cost, from API usage.cost (USD) | 1.77 | 0.4764 | 0.0495 | 0.4872 | 2.3506 | 0.4522 | 1.0697 | n/a | n/a |
| Cost, list price x tokens (USD) | 1.77 | 0.9449 | 0.0386 | 0.4872 | 2.3506 | 0.4522 | 1.3074 | n/a | n/a |
| Judge tokens (total) | 114652 | 101234 | 102744 | 108943 | 162283 | 162011 | 105002 | 102571 | 103181 |
| Judge cost (USD) | 0.0209 | 0.0182 | 0.0179 | 0.0199 | 0.0302 | 0.0303 | 0.0179 | 0.0202 | 0.0196 |
| Rubric: concepts | 100.0% [97.1, 100.0] | 98.5% [94.6, 99.6] | 99.2% [95.8, 99.9] | 100.0% [97.1, 100.0] | 97.7% [93.4, 99.2] | 99.2% [95.8, 99.9] | 98.5% [94.6, 99.6] | 40.0% [32.0, 48.6] | 50.0% [41.5, 58.5] |
| Rubric: action | 99.2% [95.8, 99.9] | 96.9% [92.4, 98.8] | 95.4% [90.3, 97.9] | 96.9% [92.4, 98.8] | 93.1% [87.4, 96.3] | 93.8% [88.3, 96.8] | 98.5% [94.6, 99.6] | 76.2% [68.1, 82.7] | 68.5% [60.0, 75.8] |
| Rubric: safe_tone | 100.0% [97.1, 100.0] | 100.0% [97.1, 100.0] | 100.0% [97.1, 100.0] | 100.0% [97.1, 100.0] | 100.0% [97.1, 100.0] | 99.2% [95.8, 99.9] | 99.2% [95.8, 99.9] | 100.0% [97.1, 100.0] | 90.8% [84.6, 94.6] |
| Rubric: readable | 55.4% [46.8, 63.7] | 90.0% [83.6, 94.1] | 60.8% [52.2, 68.7] | 16.2% [10.8, 23.4] | 38.5% [30.5, 47.0] | 43.1% [34.9, 51.7] | 59.2% [50.6, 67.3] | 83.1% [75.7, 88.6] | 40.8% [32.7, 49.4] |

| Trap type | n | claude-opus-5.5 | deepseek-v4-pro-0813 | deepseek-v4.1-flash-1017 | gemini-4-argon | gpt-6-astra | gpt-6.1-sol | grok-4.7 | llama3.2-3b-instruct-q4km | qwen2.5-1.5b-instruct-q4km |
|---|---|---|---|---|---|---|---|---|---|---|
| unit_trap | 13 | 0.0% [0.0, 22.8] | 0.0% [0.0, 22.8] | 0.0% [0.0, 22.8] | 0.0% [0.0, 22.8] | 0.0% [0.0, 22.8] | 0.0% [0.0, 22.8] | 0.0% [0.0, 22.8] | 84.6% [57.8, 95.7] | 92.3% [66.7, 98.6] |
| sex_range | 11 | 0.0% [0.0, 25.9] | 0.0% [0.0, 25.9] | 0.0% [0.0, 25.9] | 0.0% [0.0, 25.9] | 0.0% [0.0, 25.9] | 0.0% [0.0, 25.9] | 0.0% [0.0, 25.9] | 90.9% [62.3, 98.4] | 81.8% [52.3, 94.9] |
| pregnancy | 6 | 0.0% [0.0, 39.0] | 0.0% [0.0, 39.0] | 0.0% [0.0, 39.0] | 0.0% [0.0, 39.0] | 0.0% [0.0, 39.0] | 0.0% [0.0, 39.0] | 0.0% [0.0, 39.0] | 33.3% [9.7, 70.0] | 50.0% [18.8, 81.2] |
| artifact | 12 | 0.0% [0.0, 24.3] | 0.0% [0.0, 24.3] | 8.3% [1.5, 35.4] | 0.0% [0.0, 24.3] | 0.0% [0.0, 24.3] | 0.0% [0.0, 24.3] | 0.0% [0.0, 24.3] | 100.0% [75.7, 100.0] | 58.3% [32.0, 80.7] |
| athlete | 5 | 0.0% [0.0, 43.4] | 0.0% [0.0, 43.4] | 0.0% [0.0, 43.4] | 0.0% [0.0, 43.4] | 0.0% [0.0, 43.4] | 0.0% [0.0, 43.4] | 0.0% [0.0, 43.4] | 20.0% [3.6, 62.4] | 80.0% [37.6, 96.4] |


## Limits
Synthetic, rule-generated reports. One prompt and one run per model. Urgency tiers are the author's calls (lifter, TG, hemolysis,
EDTA are debatable). Frontier models are at the ceiling, so differences under about 5 points are inside the CIs.
