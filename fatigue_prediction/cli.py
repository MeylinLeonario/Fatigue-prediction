"""Command-line entry points with machine-readable provenance and diagnostics."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import platform

from .data import RECORD, download, load
from .features import build
from .models import associations, bootstrap_difference, evaluate, longitudinal_baseline


def run(data_dir, output, folds=5, seed=42, algorithms=("linear",), bootstrap=2000):
    datasets, provenance = load(data_dir)
    frame, excluded, audit = build(datasets)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output / "model_frame.csv", index=False)
    excluded.to_csv(output / "ambiguous_ratings.csv", index=False)
    frame.groupby(["session", "session_future"]).size().rename("n").to_csv(output / "transitions.csv")
    (output / "mixed_baseline.txt").write_text(longitudinal_baseline(frame), encoding="utf-8")
    summary = []
    for cohort, names in [("behavior", ("M0", "M1")), ("multimodal", ("M0", "M1", "M2", "M3"))]:
        for algorithm in algorithms:
            scores, folds_df, predictions = evaluate(frame, names, algorithm, folds, seed)
            tag = f"{cohort}_{algorithm}"
            scores.to_csv(output / f"{tag}_metrics.csv", index=False)
            folds_df.to_csv(output / f"{tag}_folds.csv", index=False)
            predictions.to_csv(output / f"{tag}_predictions.csv", index=False)
            errors = predictions.assign(residual_M0=predictions.fatigue_future - predictions.pred_M0)
            errors["abs_error_M0"] = errors.residual_M0.abs()
            errors.sort_values("abs_error_M0", ascending=False).to_csv(output / f"{tag}_errors.csv", index=False)
            errors.groupby(["session", "condition"]).agg(n=("abs_error_M0", "size"), MAE=("abs_error_M0", "mean")).to_csv(output / f"{tag}_error_groups.csv")
            if bootstrap:
                for name in names[1:]:
                    draws = bootstrap_difference(predictions, name, repeats=bootstrap, seed=seed)
                    draws.quantile([.025, .5, .975]).to_csv(output / f"{tag}_{name}_conditional_bootstrap.csv")
            summary.extend({"cohort": cohort, "algorithm": algorithm, **row} for row in scores.to_dict("records"))
        texts = associations(frame, names)
        (output / f"{cohort}_associations.txt").write_text("\n\n".join(f"{name}\n{text}" for name, text in texts.items()), encoding="utf-8")
    audit.update({"source": RECORD, "provenance": provenance, "seed": seed, "folds": folds,
                  "algorithms": list(algorithms), "bootstrap_repeats": bootstrap,
                  "python": platform.python_version(),
                  "versions": {p: importlib.metadata.version(p) for p in ["numpy", "pandas", "scikit-learn", "statsmodels"]}})
    (output / "audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    import pandas as pd
    pd.DataFrame(summary).to_csv(output / "comparison.csv", index=False)
    return frame, pd.DataFrame(summary), audit


def main():
    parser = argparse.ArgumentParser(description="Predicción exploratoria de fatiga; Zenodo 6795446")
    sub = parser.add_subparsers(dest="command", required=True)
    get = sub.add_parser("download", help="Descarga y verifica los CSV originales")
    get.add_argument("--data-dir", type=Path, default=Path("data"))
    get.add_argument("--all", action="store_true", help="Incluye pupila y decisiones; no se modelan todavía")
    analyze = sub.add_parser("run", help="Construye transiciones y evalúa por participante")
    analyze.add_argument("--data-dir", type=Path, default=Path("data"))
    analyze.add_argument("--output", type=Path, default=Path("results"))
    analyze.add_argument("--folds", type=int, default=5)
    analyze.add_argument("--seed", type=int, default=42)
    analyze.add_argument("--rf", action="store_true")
    analyze.add_argument("--bootstrap", type=int, default=2000)
    args = parser.parse_args()
    try:
        if args.command == "download":
            download(args.data_dir, args.all)
        else:
            if args.bootstrap < 0:
                parser.error("--bootstrap no puede ser negativo")
            _, summary, _ = run(args.data_dir, args.output, args.folds, args.seed,
                                ("linear", "rf") if args.rf else ("linear",), args.bootstrap)
            print(summary.to_string(index=False))
    except (ValueError, FileNotFoundError, OSError) as error:
        parser.exit(1, f"Error: {error}\n")
