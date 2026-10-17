"""Generate synthetic lab-report cases with an answer key.

No real patient data. Every value is synthetic. Reference ranges come from the
ABIM Laboratory Test Reference Ranges (Jan 2026) unless a case says otherwise;
interpretation and urgency thresholds cite the sources in SOURCES (see sources.md).
"""
import json, random
from pathlib import Path

R = random.Random(20261016)

# ---- Reference ranges (ABIM Jan 2026, conventional units). sex-specific as (F, M) ----
RANGES = {
    "WBC": (4.0, 11.0, "x10^3/uL"), "Hemoglobin": {"F": (12.0, 16.0), "M": (14.0, 18.0), "unit": "g/dL"},
    "Hematocrit": {"F": (37, 47), "M": (42, 50), "unit": "%"}, "MCV": (80, 98, "fL"),
    "Platelets": (150, 450, "x10^3/uL"), "Sodium": (136, 145, "mEq/L"), "Potassium": (3.5, 5.0, "mEq/L"),
    "Chloride": (98, 106, "mEq/L"), "Bicarbonate": (23, 28, "mEq/L"), "BUN": (8, 20, "mg/dL"),
    "Creatinine": {"F": (0.50, 1.10), "M": (0.70, 1.30), "unit": "mg/dL"}, "Glucose (fasting)": (70, 99, "mg/dL"),
    "Calcium": (8.6, 10.2, "mg/dL"), "Albumin": (3.5, 5.5, "g/dL"), "ALT": (10, 40, "U/L"), "AST": (10, 40, "U/L"),
    "Alkaline phosphatase": (30, 120, "U/L"), "Total bilirubin": (0.3, 1.0, "mg/dL"),
    "TSH": (0.5, 4.0, "mU/L"), "Free T4": (0.8, 1.8, "ng/dL"), "Ferritin": {"F": (24, 307), "M": (24, 336), "unit": "ng/mL"},
    "Iron": (50, 150, "ug/dL"), "Transferrin saturation": (20, 50, "%"), "Hemoglobin A1c": (4.0, 5.6, "%"),
    "Total cholesterol": (None, 200, "mg/dL"), "LDL cholesterol": (None, 100, "mg/dL"),
    "HDL cholesterol": {"F": (50, None), "M": (40, None), "unit": "mg/dL"}, "Triglycerides": (None, 150, "mg/dL"),
    "CK": {"F": (30, 135), "M": (55, 170), "unit": "U/L"}, "Magnesium": (1.6, 2.6, "mg/dL"),
    "hs-Troponin I": {"F": (None, 15), "M": (None, 20), "unit": "ng/L"}, "Lipase": (10, 140, "U/L"),
    "pH (arterial)": (7.38, 7.44, ""), "PaCO2": (38, 42, "mm Hg"), "PaO2": (75, 100, "mm Hg"),
    "HCO3 (arterial)": (23, 26, "mEq/L"), "Vitamin B12": (200, 800, "pg/mL"),
}
NORMAL_MID = {  # plausible normal values to fill panels
    "WBC": (5.0, 9.0), "Hemoglobin": {"F": (12.8, 14.8), "M": (14.6, 16.6)}, "Hematocrit": {"F": (38, 44), "M": (43, 48)},
    "MCV": (84, 94), "Platelets": (190, 380), "Sodium": (137, 143), "Potassium": (3.8, 4.7), "Chloride": (99, 105),
    "Bicarbonate": (24, 27), "BUN": (9, 18), "Creatinine": {"F": (0.6, 0.95), "M": (0.8, 1.15)},
    "Glucose (fasting)": (75, 95), "Calcium": (8.9, 9.9), "Albumin": (3.8, 5.0), "ALT": (14, 34), "AST": (15, 33),
    "Alkaline phosphatase": (45, 105), "Total bilirubin": (0.4, 0.9), "TSH": (0.9, 3.2), "Free T4": (0.9, 1.6),
    "Ferritin": {"F": (40, 180), "M": (60, 250)}, "Iron": (65, 140), "Transferrin saturation": (24, 44),
    "Hemoglobin A1c": (4.6, 5.4), "Total cholesterol": (150, 190), "LDL cholesterol": (65, 95),
    "HDL cholesterol": {"F": (55, 75), "M": (45, 65)}, "Triglycerides": (60, 140), "CK": {"F": (50, 120), "M": (70, 160)},
    "Magnesium": (1.8, 2.4), "hs-Troponin I": {"F": (2, 8), "M": (2, 10)}, "Lipase": (20, 60),
    "pH (arterial)": (7.39, 7.43), "PaCO2": (38.5, 41.5), "PaO2": (85, 98), "HCO3 (arterial)": (23.5, 25.5),
    "Vitamin B12": (300, 700),
}
DEC = {"WBC": 1, "Hemoglobin": 1, "Hematocrit": 0, "MCV": 0, "Platelets": 0, "Sodium": 0, "Potassium": 1, "Chloride": 0,
       "Bicarbonate": 0, "BUN": 0, "Creatinine": 2, "Glucose (fasting)": 0, "Calcium": 1, "Albumin": 1, "ALT": 0, "AST": 0,
       "Alkaline phosphatase": 0, "Total bilirubin": 1, "TSH": 2, "Free T4": 2, "Ferritin": 0, "Iron": 0,
       "Transferrin saturation": 0, "Hemoglobin A1c": 1, "Total cholesterol": 0, "LDL cholesterol": 0, "HDL cholesterol": 0,
       "Triglycerides": 0, "CK": 0, "Magnesium": 1, "hs-Troponin I": 0, "Lipase": 0, "pH (arterial)": 2, "PaCO2": 0,
       "PaO2": 0, "HCO3 (arterial)": 0, "Vitamin B12": 0}
PANELS = {
    "CBC": ["WBC", "Hemoglobin", "Hematocrit", "MCV", "Platelets"],
    "BMP": ["Sodium", "Potassium", "Chloride", "Bicarbonate", "BUN", "Creatinine", "Glucose (fasting)", "Calcium"],
    "CMP": ["Sodium", "Potassium", "Chloride", "Bicarbonate", "BUN", "Creatinine", "Glucose (fasting)", "Calcium",
            "Albumin", "ALT", "AST", "Alkaline phosphatase", "Total bilirubin"],
    "Lipid": ["Total cholesterol", "LDL cholesterol", "HDL cholesterol", "Triglycerides"],
    "Thyroid": ["TSH", "Free T4"], "Iron": ["Iron", "Ferritin", "Transferrin saturation"],
    "A1c": ["Hemoglobin A1c"], "ABG": ["pH (arterial)", "PaCO2", "PaO2", "HCO3 (arterial)"],
}
# SI conversions (factor multiplies conventional value), and SI ranges derived by the same factor
SI = {"Glucose (fasting)": (1 / 18.016, "mmol/L", 1), "Creatinine": (88.4, "umol/L", 0), "Calcium": (0.2495, "mmol/L", 2),
      "Hemoglobin": (10, "g/L", 0), "Total cholesterol": (0.02586, "mmol/L", 1), "LDL cholesterol": (0.02586, "mmol/L", 1),
      "HDL cholesterol": (0.02586, "mmol/L", 1), "Triglycerides": (0.01129, "mmol/L", 1), "BUN": (0.357, "mmol/L urea", 1),
      "Total bilirubin": (17.1, "umol/L", 0), "Albumin": (10, "g/L", 0), "Magnesium": (0.4114, "mmol/L", 2)}
LT_STRICT = {"Total cholesterol", "LDL cholesterol", "Triglycerides"}
URG = ["routine", "soon", "urgent", "emergency"]


def rng_for(name, sex):
    r = RANGES[name]
    if isinstance(r, dict):
        lo, hi = r[sex]; return lo, hi, r["unit"]
    return r


def range_text(name, sex, si=False, both_sexes=False, unit_override=None):
    def fmt(lo, hi, f=1.0, d=None):
        d = DEC[name] if d is None else d
        g = lambda v: f"{v * f:.{d}f}"
        if lo is None: return (f"<{g(hi)}" if name in LT_STRICT else f"<={g(hi)}") if hi else ""
        if hi is None: return f">={g(lo)}"
        return f"{g(lo)}-{g(hi)}"
    f, d = (SI[name][0], SI[name][2]) if si else (1.0, None)
    r = RANGES[name]
    if isinstance(r, dict) and both_sexes:
        return f"F {fmt(*r['F'], f, d)}; M {fmt(*r['M'], f, d)}"
    lo, hi, _ = rng_for(name, sex)
    return fmt(lo, hi, f, d)


def flag(name, val, sex):
    lo, hi, _ = rng_for(name, sex)
    if lo is not None and val < lo: return "L"
    if hi is not None and (val >= hi if name in LT_STRICT else val > hi): return "H"
    return "N"


def normal_val(name, sex):
    m = NORMAL_MID[name]
    lo, hi = (m[sex] if isinstance(m, dict) else m)
    return round(R.uniform(lo, hi), DEC[name])


class Case:
    def __init__(self, cid, category, age, sex, context, panels, overrides, interp_terms, interpretation,
                 urgency, expl_terms, sources, tags=(), comment="", si_analytes=(), both_sexes=(), trap=None,
                 flag_override=None, extra_rows=()):
        self.d = dict(id=cid, category=category, tags=list(tags))
        names = []
        for p in panels:
            for n in PANELS[p]:
                if n not in names: names.append(n)
        for n in overrides:
            if n not in names: names.append(n)
        rows, flags, values = [], {}, {}
        for n in names:
            v = overrides.get(n, normal_val(n, sex))
            v = round(v, DEC[n])
            fl = flag(n, v, sex)
            if fl != "N": flags[n] = fl
            si = n in si_analytes
            unit = SI[n][1] if si else rng_for(n, sex)[2]
            shown = round(v * SI[n][0], SI[n][2]) if si else v
            dshown = SI[n][2] if si else DEC[n]
            rows.append(dict(analyte=n, value=shown, unit=unit, range=range_text(n, sex, si, n in both_sexes),
                             shown_str=f"{shown:.{dshown}f}"))
            values[n] = shown
        for er in extra_rows:  # qualitative rows (urinalysis etc.)
            rows.append(dict(analyte=er[0], value=er[1], unit="", range=er[2], shown_str=str(er[1])))
            if len(er) > 3 and er[3]: flags[er[0]] = er[3]
        if flag_override: flags.update(flag_override)
        flags = {k: v for k, v in flags.items() if v != "N"}
        lines = [f"Patient: {age}-year-old {'female' if sex == 'F' else 'male'}. {context}".strip()]
        if comment: lines.append(f"Lab comment: {comment}")
        lines.append("Test | Result | Units | Reference range")
        for r_ in rows:
            lines.append(f"{r_['analyte']} | {r_['shown_str']} | {r_['unit']} | {r_['range']}")
        self.d.update(patient=dict(age=age, sex=sex, context=context), report=dict(rows=rows, comment=comment),
                      report_text="\n".join(lines),
                      key=dict(flags=flags, interpretation=interpretation, interpretation_terms=interp_terms,
                               urgency=urgency, explanation_terms=expl_terms, trap=trap, sources=list(sources),
                               values=values))


def u(lo, hi, d=1):
    return round(R.uniform(lo, hi), d)


def build():
    cases = []
    def add(*a, **k):
        cases.append(Case(f"c{len(cases) + 1:03d}", *a, **k).d)

    # 1. Normal panels (routine)
    for i in range(8):
        sex = "F" if i % 2 else "M"; age = R.randint(22, 64)
        pan = [["CBC", "CMP"], ["CBC", "BMP", "Lipid"], ["CMP", "Thyroid"], ["CBC", "Iron"]][i % 4]
        add("normal", age, sex, "Annual physical, no symptoms.", pan, {}, [["normal", "within", "no abnormal", "unremarkable"]],
            "All results within reference range.", "routine", [["normal", "within", "healthy range", "no concern"]], ["ABIM2026"], tags=["normal"])
    # 2. Iron deficiency anemia (soon)
    for i in range(5):
        sex = "F"; age = R.randint(19, 45)
        add("iron_deficiency_anemia", age, sex, "Fatigue, heavy menstrual periods.", ["CBC", "Iron"],
            {"Hemoglobin": u(9.0, 10.8), "Hematocrit": u(28, 33, 0), "MCV": u(68, 76, 0), "Ferritin": u(3, 10, 0),
             "Iron": u(18, 38, 0), "Transferrin saturation": u(4, 11, 0)},
            [["iron deficiency", "iron-deficiency"]], "Microcytic anemia with low ferritin: iron deficiency anemia.",
            "soon", [["iron"], ["anemia", "red blood cell", "low hemoglobin", "hemoglobin"]], ["ABIM2026", "CDC_MMWR_1998_IRON"])
    # 3. B12 deficiency macrocytic (soon)
    for i in range(3):
        sex = R.choice("FM"); age = R.randint(55, 78)
        add("b12_deficiency", age, sex, "On metformin 8 years; tingling in feet.", ["CBC"],
            {"Hemoglobin": u(9.5, 11.0) if sex == "F" else u(10.5, 12.5), "MCV": u(108, 118, 0), "Vitamin B12": u(90, 160, 0)},
            [["b12", "cobalamin"]], "Macrocytic anemia with low B12 (metformin is a known risk).", "soon",
            [["b12", "vitamin b-12", "cobalamin"]], ["ABIM2026"])
    # 4. Thyroid
    for i in range(3):
        sex = "F"; age = R.randint(30, 60)
        add("overt_hypothyroidism", age, sex, "Weight gain, cold intolerance.", ["Thyroid"],
            {"TSH": u(18, 45, 2), "Free T4": u(0.35, 0.6, 2)}, [["hypothyroid", "underactive thyroid"]],
            "High TSH with low free T4: primary hypothyroidism.", "soon", [["thyroid"], ["underactive", "hypothyroid", "low thyroid", "not making enough", "not producing enough", "slow"]], ["ABIM2026"])
    for i in range(3):
        sex = R.choice("FM"); age = R.randint(30, 65)
        add("subclinical_hypothyroidism", age, sex, "Routine screening, no symptoms.", ["Thyroid"],
            {"TSH": u(4.6, 7.5, 2), "Free T4": u(0.95, 1.4, 2)}, [["subclinical"]],
            "Mildly high TSH with normal free T4: subclinical hypothyroidism; repeat in weeks.", "routine",
            [["thyroid"], ["repeat", "recheck", "follow"]], ["ABIM2026"])
    for i in range(3):
        sex = "F"; age = R.randint(22, 50)
        add("hyperthyroidism", age, sex, "Palpitations, weight loss, heat intolerance.", ["Thyroid"],
            {"TSH": u(0.01, 0.05, 2), "Free T4": u(3.0, 4.6, 2)}, [["hyperthyroid", "overactive thyroid", "thyrotoxicosis", "graves"]],
            "Suppressed TSH with high free T4: hyperthyroidism.", "soon", [["thyroid"], ["overactive", "hyperthyroid", "too much", "excess"]], ["ABIM2026"])
    # 5. Diabetes / prediabetes / DKA
    for i in range(4):
        sex = R.choice("FM"); age = R.randint(40, 68)
        add("type2_diabetes_range", age, sex, "Routine labs; BMI 33.", ["BMP", "A1c"],
            {"Hemoglobin A1c": u(7.0, 8.8), "Glucose (fasting)": u(140, 190, 0)}, [["diabetes"]],
            "A1c >=6.5% and fasting glucose >=126 mg/dL: diabetes range (ADA).", "soon", [["diabetes", "blood sugar"]], ["ABIM2026", "ADA2026"])
    for i in range(4):
        sex = R.choice("FM"); age = R.randint(30, 60)
        add("prediabetes", age, sex, "Routine labs.", ["A1c"], {"Hemoglobin A1c": u(5.8, 6.3), "Glucose (fasting)": u(101, 118, 0)},
            [["prediabetes", "pre-diabetes", "impaired fasting"]], "A1c 5.7-6.4% / FPG 100-125: prediabetes (ADA).", "routine",
            [["prediabetes", "pre-diabetes", "higher than normal", "risk"]], ["ABIM2026", "ADA2026"])
    for i in range(4):
        sex = R.choice("FM"); age = R.randint(18, 40)
        g = u(380, 560, 0); hco3 = u(8, 13, 0); na = u(129, 134, 0)
        add("dka", age, sex, "Type 1 diabetes, vomiting, abdominal pain. Urine ketones 3+.", ["BMP"],
            {"Glucose (fasting)": g, "Bicarbonate": hco3, "Sodium": na, "Chloride": u(94, 99, 0), "Potassium": u(5.2, 5.8),
             "BUN": u(24, 34, 0)}, [["ketoacidosis", "dka"]],
            "Hyperglycemia + low bicarbonate (high anion gap) + ketones: DKA.", "emergency",
            [["emergency", "er", "911", "immediately", "right away", "hospital"]], ["ABIM2026", "ADA_CRISES_2024"],
            tags=["critical"], comment="Specimen: random (non-fasting).")
    # 6. Electrolytes
    for i in range(4):
        sex = R.choice("FM"); age = R.randint(55, 80)
        add("true_hyperkalemia", age, sex, "CKD stage 4, on lisinopril and spironolactone. Specimen not hemolyzed.", ["BMP"],
            {"Potassium": u(6.6, 7.4), "Creatinine": u(2.9, 3.8, 2), "BUN": u(48, 70, 0), "Bicarbonate": u(17, 20, 0)},
            [["hyperkalemia", "high potassium"]], "Severe true hyperkalemia (>=6.0 critical) in CKD on RAAS blockade.", "emergency",
            [["emergency", "er", "911", "immediately", "right away", "hospital"], ["potassium"]], ["ABIM2026", "MAYO_CRIT", "STATPEARLS_HYPERK"], tags=["critical"])
    for i in range(5):
        sex = R.choice("FM"); age = R.randint(20, 50)
        add("hemolyzed_potassium", age, sex, "Healthy, routine labs, no medications.", ["BMP"],
            {"Potassium": u(5.6, 6.3)}, [["hemoly", "pseudohyperkalemia", "spurious", "falsely", "artifact", "redraw", "repeat"]],
            "Isolated high K in a hemolyzed sample: likely pseudohyperkalemia; repeat draw.", "soon",
            [["repeat", "redraw", "retest", "recheck"]], ["ABIM2026", "STATPEARLS_HYPERK"], tags=["artifact", "trap"],
            comment="Moderate hemolysis noted (H-index 3+). Potassium may be falsely elevated.", trap="Potassium")
    for i in range(3):
        sex = R.choice("FM"); age = R.randint(60, 85)
        add("severe_hyponatremia", age, sex, "Confusion for 1 day; on hydrochlorothiazide.", ["BMP"],
            {"Sodium": u(112, 119, 0), "Chloride": u(80, 88, 0)}, [["hyponatremia", "low sodium"]],
            "Severe symptomatic hyponatremia (<=120 critical).", "emergency",
            [["emergency", "er", "911", "immediately", "right away", "hospital"], ["sodium", "salt"]], ["ABIM2026", "MAYO_CRIT"], tags=["critical"])
    for i in range(3):
        sex = R.choice("FM"); age = R.randint(40, 75)
        add("mild_hyponatremia", age, sex, "No symptoms; routine labs.", ["BMP"], {"Sodium": u(132, 134, 0)},
            [["hyponatremia", "low sodium", "mildly low sodium"]], "Mild asymptomatic hyponatremia.", "routine",
            [["sodium", "salt"]], ["ABIM2026"])
    for i in range(3):
        sex = R.choice("FM"); age = R.randint(55, 80)
        add("severe_hypercalcemia", age, sex, "Nausea, confusion, weight loss; smoker.", ["CMP"],
            {"Calcium": u(13.6, 15.0), "Albumin": u(3.6, 4.1)}, [["hypercalcemia", "high calcium"]],
            "Severe hypercalcemia (>=13 critical), malignancy concern.", "emergency",
            [["emergency", "er", "911", "immediately", "right away", "hospital"], ["calcium"]], ["ABIM2026", "MAYO_CRIT"], tags=["critical"])
    # 7. Kidney / athletes
    for i in range(4):
        sex = R.choice("FM"); age = R.randint(50, 80)
        add("aki", age, sex, "Baseline creatinine 0.9 mg/dL six months ago; 4 days of diarrhea, on ibuprofen.", ["BMP"],
            {"Creatinine": u(2.8, 3.6, 2), "BUN": u(55, 80, 0), "Potassium": u(5.1, 5.6)},
            [["acute kidney", "aki", "kidney injury", "renal failure"]], "Acute kidney injury (>3x baseline), prerenal/NSAID.", "urgent",
            [["kidney"], ["today", "same day", "promptly", "urgent", "right away", "as soon as"]], ["ABIM2026"])
    for i in range(5):
        sex = "M"; age = R.randint(19, 30)
        add("lifter_benign_ck_creatinine", age, sex,
            "Competitive powerlifter, 95 kg, heavy squat session 36 h before draw, takes creatine 5 g/day. No symptoms, urine normal color.",
            ["CMP"], {"CK": u(1400, 3200, 0), "Creatinine": u(1.32, 1.48, 2), "AST": u(45, 70, 0), "ALT": u(30, 39, 0)},
            [["exercise", "exertion", "training", "workout", "muscle mass", "creatine"]],
            "Post-exercise CK/AST rise and muscle-mass/creatine-related creatinine; benign pattern, recheck after rest (consider cystatin C).", "routine",
            [["exercise", "workout", "training", "lifting"], ["recheck", "repeat", "retest", "cystatin"]],
            ["ABIM2026", "PMC4437836_RHABDO", "PMC6580786_EXERTIONAL"], tags=["athlete", "trap"], trap="CK")
    for i in range(3):
        sex = "M"; age = R.randint(19, 32)
        add("exertional_rhabdo", age, sex, "Did a first-ever 300-rep CrossFit workout 2 days ago; severe thigh pain, cola-colored urine.", ["BMP"],
            {"CK": u(48000, 95000, 0), "Creatinine": u(1.9, 2.6, 2), "Potassium": u(5.4, 6.1), "AST": u(600, 1100, 0)},
            [["rhabdomyolysis", "rhabdo"]], "Exertional rhabdomyolysis with AKI.", "emergency",
            [["emergency", "er", "911", "immediately", "right away", "hospital"], ["muscle"]],
            ["ABIM2026", "PMC6580786_EXERTIONAL", "MAYO_CRIT"], tags=["athlete", "critical"],
            extra_rows=[("Urine blood (dipstick)", "3+", "Negative", "H"), ("Urine RBC", "0-2 /hpf", "0-2 /hpf")])
    # 8. Sex-specific range traps (both ranges printed)
    for i in range(4):
        age = R.randint(25, 55)
        add("sex_range_normal_female_hb", age, "F", "Routine labs.", ["CBC"], {"Hemoglobin": u(12.4, 13.4), "Hematocrit": u(38, 41, 0)},
            [["normal", "within", "no abnormal", "unremarkable"]], "Hb normal for a female (would be low for a male).", "routine",
            [["normal", "within", "healthy range"]], ["ABIM2026"], tags=["sex_range", "trap"], both_sexes=["Hemoglobin", "Hematocrit"], trap="Hemoglobin")
    for i in range(4):
        age = R.randint(25, 55)
        add("sex_range_low_male_hb", age, "M", "Routine labs; mild fatigue.", ["CBC"], {"Hemoglobin": u(12.6, 13.4), "Hematocrit": u(38, 41, 0)},
            [["anemia", "low hemoglobin"]], "Hb low for a male (would be normal for a female): mild anemia, evaluate.", "soon",
            [["anemia", "low hemoglobin", "red blood cell", "hemoglobin"]], ["ABIM2026"], tags=["sex_range", "trap"], both_sexes=["Hemoglobin", "Hematocrit"], trap="Hemoglobin")
    for i in range(3):
        age = R.randint(30, 60)
        add("sex_range_high_female_creat", age, "F", "Routine labs, petite build.", ["BMP"], {"Creatinine": u(1.18, 1.28, 2)},
            [["kidney", "renal", "creatinine"]], "Creatinine high for a female (normal for a male): reduced kidney function, recheck/eGFR.", "soon",
            [["kidney"]], ["ABIM2026"], tags=["sex_range", "trap"], both_sexes=["Creatinine"], trap="Creatinine")
    # 9. Unit traps (SI units printed with SI ranges)
    for i in range(4):
        sex = R.choice("FM"); age = R.randint(25, 60)
        add("unit_si_normal", age, sex, "Results from a lab in Canada (SI units). Routine labs.", ["BMP", "Lipid"], {},
            [["normal", "within", "no abnormal", "unremarkable"]], "All results normal in SI units.", "routine",
            [["normal", "within", "healthy range"]], ["ABIM2026", "SI_CONV"], tags=["unit_trap", "trap"],
            si_analytes=["Glucose (fasting)", "Creatinine", "Calcium", "BUN", "Total cholesterol", "LDL cholesterol", "HDL cholesterol", "Triglycerides"],
            trap="Glucose (fasting)")
    for i in range(3):
        sex = R.choice("FM"); age = R.randint(40, 70)
        add("unit_si_diabetes", age, sex, "Results from a lab in the UK (SI units).", ["BMP"], {"Glucose (fasting)": u(150, 190, 0)},
            [["diabetes", "high blood sugar", "hyperglycemia"]], "Fasting glucose 8.3-10.5 mmol/L = 150-190 mg/dL: diabetes range.", "soon",
            [["sugar", "glucose", "diabetes"]], ["ABIM2026", "ADA2026", "SI_CONV"], tags=["unit_trap", "trap"],
            si_analytes=["Glucose (fasting)", "Creatinine", "Calcium", "BUN"], trap="Glucose (fasting)")
    for i in range(3):
        sex = R.choice("FM"); age = R.randint(50, 80)
        add("unit_si_hypoglycemia", age, sex, "On insulin; sweaty and shaky at time of draw. Results in SI units.", ["BMP"],
            {"Glucose (fasting)": u(36, 46, 0)}, [["hypoglycemia", "low blood sugar", "low glucose"]],
            "Glucose 2.0-2.6 mmol/L = 36-46 mg/dL: critical hypoglycemia.", "emergency",
            [["sugar", "glucose"], ["emergency", "immediately", "right away", "911", "now"]], ["ABIM2026", "MAYO_CRIT", "SI_CONV"],
            tags=["unit_trap", "trap", "critical"], si_analytes=["Glucose (fasting)", "Creatinine", "Calcium", "BUN"], trap="Glucose (fasting)")
    for i in range(3):
        sex = "M"; age = R.randint(25, 50)
        add("unit_si_creatinine_normal", age, sex, "Results in SI units. Routine labs.", ["BMP"], {"Creatinine": u(0.9, 1.15, 2)},
            [["normal", "within", "no abnormal", "unremarkable"]], "Creatinine 80-102 umol/L is normal.", "routine",
            [["normal", "within", "healthy range"]], ["ABIM2026", "SI_CONV"], tags=["unit_trap", "trap"],
            si_analytes=["Glucose (fasting)", "Creatinine", "Calcium", "BUN"], trap="Creatinine")
    # 10. Pregnancy
    for i in range(3):
        age = R.randint(24, 36)
        add("pregnancy_physiologic_hb", age, "F", "Pregnant, 29 weeks (third trimester). Feels well. Taking prenatal vitamins.", ["CBC"],
            {"Hemoglobin": u(11.2, 11.7), "Hematocrit": u(34, 36, 0), "MCV": u(86, 92, 0), "WBC": u(10.0, 12.5)},
            [["pregnan", "physiologic", "dilution", "expected", "normal"]],
            "Hb below nonpregnant range but >=11.0 in 3rd trimester: physiologic hemodilution, not anemia by CDC pregnancy cutoff.", "routine",
            [["pregnan"]], ["ABIM2026", "CDC_MMWR_1989_ANEMIA"], tags=["pregnancy", "trap"], trap="Hemoglobin")
    for i in range(3):
        age = R.randint(24, 38)
        add("pregnancy_alp", age, "F", "Pregnant, 34 weeks. No itching, no symptoms.", ["CMP"],
            {"Alkaline phosphatase": u(190, 260, 0), "Albumin": u(3.0, 3.4)},
            [["placenta", "pregnan", "expected", "physiologic", "normal"]],
            "High ALP and mildly low albumin are expected in late pregnancy (placental ALP, hemodilution).", "routine",
            [["pregnan"]], ["ABIM2026", "PREG_ALP"], tags=["pregnancy", "trap"], trap="Alkaline phosphatase")
    for i in range(2):
        age = R.randint(24, 36)
        add("pregnancy_true_anemia", age, "F", "Pregnant, 14 weeks (second trimester). Fatigue.", ["CBC", "Iron"],
            {"Hemoglobin": u(8.6, 9.6), "Hematocrit": u(27, 30, 0), "MCV": u(70, 76, 0), "Ferritin": u(4, 9, 0), "Transferrin saturation": u(5, 10, 0), "Iron": u(20, 35, 0)},
            [["iron deficiency", "iron-deficiency"]], "Hb below 10.5 second-trimester cutoff with low ferritin: iron deficiency anemia of pregnancy.", "soon",
            [["iron"], ["pregnan"]], ["ABIM2026", "CDC_MMWR_1989_ANEMIA"], tags=["pregnancy"])
    # 11. Artifacts
    for i in range(4):
        sex = R.choice("FM"); age = R.randint(25, 65)
        add("pseudothrombocytopenia", age, sex, "Routine labs; no bruising or bleeding.", ["CBC"], {"Platelets": u(38, 70, 0)},
            [["clump", "pseudothrombocytopenia", "artifact", "spurious", "falsely", "citrate"]],
            "Low platelet count with clumps seen: EDTA pseudothrombocytopenia; repeat in citrate tube.", "soon",
            [["repeat", "redraw", "retest", "recheck"]], ["ABIM2026", "STATPEARLS_THROMBOCYTOPENIA", "CROATIA_PTCP_2024"],
            tags=["artifact", "trap"], comment="Platelet clumps seen on smear (EDTA tube).", trap="Platelets")
    for i in range(3):
        sex = R.choice("FM"); age = R.randint(40, 80)
        add("edta_contamination", age, sex, "Outpatient, feels well, no kidney disease, no medications.", ["CMP"],
            {"Potassium": u(8.6, 10.5), "Calcium": u(4.8, 6.0), "Alkaline phosphatase": u(15, 26, 0)},
            [["edta", "contamination", "artifact", "spurious", "falsely", "redraw", "repeat"]],
            "Very high K with very low Ca and low ALP in a well patient: K-EDTA contamination; immediate redraw.", "urgent",
            [["repeat", "redraw", "retest", "recheck"]], ["ABIM2026", "CORNES2008_EDTA", "LORDE_KEDTA"], tags=["artifact", "trap"], trap="Potassium")
    # 12. Critical hematology
    for i in range(3):
        sex = R.choice("FM"); age = R.randint(40, 80)
        add("severe_anemia", age, sex, "Black stools for 3 days, dizzy on standing.", ["CBC"],
            {"Hemoglobin": u(5.4, 6.4), "Hematocrit": u(17, 20, 0), "MCV": u(76, 84, 0)},
            [["bleed", "anemia", "blood loss", "gi bleed", "gastrointestinal"]], "Severe anemia with melena: GI bleed.", "emergency",
            [["emergency", "er", "911", "immediately", "right away", "hospital"]], ["ABIM2026", "MAYO_CRIT"], tags=["critical"])
    for i in range(3):
        sex = R.choice("FM"); age = R.randint(20, 70)
        add("severe_thrombocytopenia", age, sex, "New petechiae and gum bleeding. No clumps on smear.", ["CBC"], {"Platelets": u(4, 12, 0)},
            [["thrombocytopenia", "low platelet", "itp"]], "Severe true thrombocytopenia with bleeding.", "emergency",
            [["emergency", "er", "911", "immediately", "right away", "hospital"], ["platelet"]], ["ABIM2026", "MAYO_CRIT"], tags=["critical"],
            comment="Smear reviewed: no platelet clumps.")
    # 13. Liver, lipids, cardiac
    for i in range(3):
        sex = R.choice("FM"); age = R.randint(25, 55)
        add("acute_hepatitis", age, sex, "Took acetaminophen ~12 g over 2 days for toothache; nausea.", ["CMP"],
            {"ALT": u(1800, 4200, 0), "AST": u(1500, 3900, 0), "Total bilirubin": u(1.6, 2.6)},
            [["liver injury", "hepatitis", "acetaminophen", "hepatotoxicity", "liver damage"]], "Acute hepatocellular injury, acetaminophen toxicity.", "emergency",
            [["emergency", "er", "911", "immediately", "right away", "hospital", "poison"], ["liver"]], ["ABIM2026"], tags=["critical"])
    for i in range(3):
        sex = R.choice("FM"); age = R.randint(25, 45)
        add("familial_hypercholesterolemia", age, sex, "Father had MI at 44. Routine lipids.", ["Lipid"],
            {"LDL cholesterol": u(205, 260, 0), "Total cholesterol": u(285, 340, 0)},
            [["familial", "genetic", "inherited", "hypercholesterolemia", "high ldl", "high cholesterol"]],
            "LDL >=190: severe hypercholesterolemia, possible familial hypercholesterolemia.", "soon",
            [["cholesterol", "ldl"]], ["ABIM2026"])
    for i in range(3):
        sex = R.choice("FM"); age = R.randint(35, 60)
        add("severe_hypertriglyceridemia", age, sex, "Heavy alcohol use; poorly controlled diabetes. No abdominal pain.", ["Lipid"],
            {"Triglycerides": u(1100, 1900, 0)}, [["triglyceride", "pancreatitis"]],
            "Very high triglycerides (>1000) with pancreatitis risk.", "soon", [["triglyceride", "fat"], ["pancreatitis", "pancreas"]], ["ABIM2026"],
            comment="Specimen lipemic.")
    for i in range(3):
        sex = R.choice("FM"); age = R.randint(50, 75)
        add("elevated_troponin", age, sex, "Chest pressure for 2 hours, sweating.", ["BMP"],
            {"hs-Troponin I": u(250, 900, 0)}, [["heart attack", "myocardial", "mi", "cardiac injury", "heart damage", "acs"]],
            "Markedly elevated hs-troponin with chest pain: suspected MI.", "emergency",
            [["emergency", "er", "911", "immediately", "right away", "hospital"], ["heart"]], ["ABIM2026", "UDMI4"], tags=["critical"])
    # 14. ABG and UA
    for i in range(3):
        sex = R.choice("FM"); age = R.randint(55, 80)
        add("acute_resp_acidosis", age, sex, "COPD, drowsy, on home oxygen turned up to 6 L.", ["ABG"],
            {"pH (arterial)": u(7.18, 7.25, 2), "PaCO2": u(68, 82, 0), "PaO2": u(55, 68, 0), "HCO3 (arterial)": u(28, 31, 0)},
            [["respiratory acidosis", "hypercapnia", "co2 retention", "hypercapnic"]], "Acute (on chronic) respiratory acidosis.", "emergency",
            [["emergency", "er", "911", "immediately", "right away", "hospital"]], ["ABIM2026", "MAYO_CRIT"], tags=["critical"])
    for i in range(3):
        sex = "F"; age = R.randint(20, 45)
        add("uti", age, sex, "Burning with urination for 2 days, no fever or back pain.", ["CBC"], {},
            [["urinary tract infection", "uti", "bladder infection", "cystitis"]], "Positive nitrite and leukocyte esterase with pyuria: UTI.", "soon",
            [["infection"]], ["ABIM2026", "UA_AAFP"],
            extra_rows=[("Urine nitrite", "Positive", "Negative", "H"), ("Urine leukocyte esterase", "2+", "Negative", "H"),
                        ("Urine WBC", "25-50 /hpf", "0-5 /hpf", "H"), ("Urine blood (dipstick)", "Trace", "Negative", "H")])
    return cases


if __name__ == "__main__":
    cases = build()
    out = Path(__file__).resolve().parent.parent / "data"
    with open(out / "cases.jsonl", "w") as f:
        for c in cases:
            f.write(json.dumps({k: c[k] for k in ("id", "category", "tags", "patient", "report_text")}) + "\n")
    with open(out / "answer_key.jsonl", "w") as f:
        for c in cases:
            f.write(json.dumps({"id": c["id"], "category": c["category"], "tags": c["tags"], **c["key"]}) + "\n")
    from collections import Counter
    print(len(cases), Counter(c["key"]["urgency"] for c in cases))
