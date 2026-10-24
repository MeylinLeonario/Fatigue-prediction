"""Conservative temporal pairing and audited session-level features."""
import pandas as pd
from .data import KEYS, validate

BEHAVIOR = ["accuracy", "median_rt", "within_session_rt_change", "within_session_accuracy_change"]


def transitions(ratings):
    ratings = validate(ratings, "ratings")
    raw = ratings.loc[ratings.question.eq("Fatigue"), KEYS + ["rating"]].copy()
    if raw.empty:
        raise ValueError("No hay respuestas Fatigue")
    ambiguous = raw.duplicated(KEYS, keep=False)
    excluded = raw.loc[ambiguous].copy()
    clean = raw.loc[~ambiguous].rename(columns={"rating": "fatigue"}).sort_values(KEYS)
    grouped = clean.groupby(KEYS[:2], sort=False)
    clean["fatigue_future"] = grouped.fatigue.shift(-1)
    clean["session_future"] = grouped.session.shift(-1)
    valid = clean.session_future.sub(clean.session).eq(1) & clean[["fatigue", "fatigue_future"]].notna().all(axis=1)
    paired = clean.loc[valid].copy()
    paired["delta_fatigue"] = paired.fatigue_future - paired.fatigue
    audit = {"fatigue_rows": len(raw), "ambiguous_rows": len(excluded),
             "missing_fatigue_rows": int(raw.rating.isna().sum()),
             "valid_transitions": len(paired), "subjects": int(paired.subject_id.nunique())}
    return paired.reset_index(drop=True), excluded, audit


def behavior(ntask):
    frame = validate(ntask, "ntask")
    order = KEYS + ["block", "trial"]
    # A tied order across tasks cannot be resolved by inventing a task sequence.
    if frame[order + ["task"]].isna().any().any() or frame.duplicated(order).any():
        raise ValueError("ntask: orden block/trial ausente o ambiguo entre tareas")
    frame = frame.sort_values(order).copy()
    # Keep all trials for accuracy denominators; invalid RTs become missing.
    frame.loc[frame.response_time.le(0), "response_time"] = float("nan")
    group = frame.groupby(KEYS, sort=False)
    position = group.cumcount()
    count = group.trial.transform("size")
    frame["half"] = position.ge(count / 2).map({False: "early", True: "late"})
    summary = frame.groupby(KEYS).agg(
        n_trials=("trial", "size"), n_performance=("performance", "count"),
        accuracy=("performance", "mean"), median_rt=("response_time", "median"),
        n_valid_rt=("response_time", "count"), n_tasks=("task", "nunique"),
    ).reset_index()
    for half in ["early", "late"]:
        part = frame.loc[frame.half.eq(half)].groupby(KEYS).agg(
            **{f"{half}_accuracy": ("performance", "mean"), f"{half}_rt": ("response_time", "median")}
        ).reset_index()
        summary = summary.merge(part, on=KEYS, how="left", validate="one_to_one")
    summary["within_session_rt_change"] = summary.late_rt - summary.early_rt
    summary["within_session_accuracy_change"] = summary.late_accuracy - summary.early_accuracy
    return summary


def spectroscopy(frame, name, value, prefix):
    frame = validate(frame, name)
    if frame.ROI.isna().any() or frame.duplicated(KEYS + ["ROI"]).any():
        raise ValueError(f"{name}: ROI ausente o duplicada; no se promedian réplicas silenciosamente")
    wide = frame.pivot(index=KEYS, columns="ROI", values=value)
    wide.columns = [f"{prefix}_{roi}" for roi in wide.columns]
    return wide.reset_index()


def build(datasets):
    paired, excluded, audit = transitions(datasets["ratings"])
    result = paired.merge(behavior(datasets["ntask"]), on=KEYS, how="left", validate="one_to_one")
    for name, value, prefix in [("glu", "Glu_tCr", "MRS_Glu_tCr"), ("dws", "ADC_log_Glu_Gln_lin", "DWS_ADC")]:
        result = result.merge(spectroscopy(datasets[name], name, value, prefix),
                              on=KEYS, how="left", validate="one_to_one")
    audit["availability"] = {c: int(result[c].notna().sum()) for c in BEHAVIOR + [c for c in result if c.startswith(("MRS_", "DWS_"))]}
    return result, excluded, audit
