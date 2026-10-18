"""
evidence_labels.py - classifies attribution ledger entries into high-level evidence labels:
Supported, Conflicting, or Insufficient evidence.

HOW IT WORKS:
1. Loads pipeline/data/processed/ledger_entries.csv.
2. Applies transparent rule-based classification:
   - Supported: Grade A or B, no contradicting modules, and source is not 'other'.
   - Conflicting: At least one graded module supports AND at least one contradicts,
     or grade B with an active contradiction.
   - Insufficient evidence: Grade C with zero supporting modules, or episode data-quality
     warning active, or source is 'other' (which is a baseline remainder).
3. Synthesizes a plain-language 'label_reason' sentence explaining the classification.
4. Saves to pipeline/data/processed/ledger_labels.csv.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
from common import tag_synthetic  # type: ignore

from config import PROCESSED  # type: ignore


def classify_entry(row: pd.Series) -> tuple[str, str]:
    source = str(row["source"])
    grade = str(row["grade"])
    sup_val = row.get("modules_supporting")
    sup_str = str(sup_val) if sup_val is not None and str(sup_val) != "nan" else ""
    con_val = row.get("modules_contradicting")
    con_str = str(con_val) if con_val is not None and str(con_val) != "nan" else ""
    notes_val = row.get("notes")
    notes = str(notes_val) if notes_val is not None and str(notes_val) != "nan" else ""
    
    sup_mods = [m.strip() for m in sup_str.split(",") if m.strip()]
    con_mods = [m.strip() for m in con_str.split(",") if m.strip()]
    
    is_bad_data = "data quality" in notes.lower() or "missing" in notes.lower()

    # Rule 1: 'other' is an unmeasured remainder
    if source == "other":
        label = "Insufficient evidence"
        reason = "Remainder category: calculated by mass-balance difference from published baseline without direct physical evidence."
        return label, reason

    # Rule 2: Conflicting evidence
    if (len(sup_mods) >= 1 and len(con_mods) >= 1) or (grade == "B" and len(con_mods) >= 1):
        label = "Conflicting"
        reason = (
            f"Evidence points in competing directions: supported by {', '.join(sup_mods)} "
            f"but contradicted by {', '.join(con_mods)}."
        )
        return label, reason

    # Rule 3: Supported
    if grade in ("A", "B") and len(con_mods) == 0:
        label = "Supported"
        modules_text = f"{', '.join(sup_mods)}" if sup_mods else "consistent baseline indicators"
        reason = f"Consistent evidence across {modules_text} with no contradicting signals (Grade {grade})."
        return label, reason

    # Rule 4: Insufficient evidence fallback
    label = "Insufficient evidence"
    if is_bad_data:
        reason = "Station coverage or air quality data completeness was insufficient during this episode to confirm attribution."
    elif len(sup_mods) == 0:
        reason = f"No independent observation modules detected distinct signals above threshold for this source (Grade {grade})."
    else:
        reason = f"Weak or isolated observation signals (Grade {grade}); attribution relies primarily on seasonal baseline."

    return label, reason


def main():
    ledger_path = PROCESSED / "ledger_entries.csv"
    if not ledger_path.exists():
        sys.exit(f"Missing {ledger_path}. Run analysis/attribution.py first.")

    df = pd.read_csv(ledger_path)
    labels = []
    reasons = []

    for _, row in df.iterrows():
        lbl, rsn = classify_entry(row)
        labels.append(lbl)
        reasons.append(rsn)

    df["label"] = labels
    df["label_reason"] = reasons

    out_path = PROCESSED / "ledger_labels.csv"
    tagged = tag_synthetic(df)
    tagged.to_csv(out_path, index=False)

    print("=" * 80)
    print(" POLLUTION BLAME LEDGER - EVIDENCE LABELS CLASSIFICATION ")
    print("=" * 80)
    summary = df.groupby(["source", "label"]).size().unstack(fill_value=0)
    print(summary.to_string())
    print("\nSample labeled rows:")
    sample_cols = ["episode_id", "source", "share_mid_pct", "grade", "label", "label_reason"]
    print(df[sample_cols].head(10).to_string(index=False))
    print(f"\nSaved {len(df)} rows -> {out_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
