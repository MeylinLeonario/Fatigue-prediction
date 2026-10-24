"""Identical participant folds and training-only preprocessing for every model."""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .features import BEHAVIOR

BASE = ["fatigue", "session", "condition"]
GLU = ["MRS_Glu_tCr_PFC"]
FEATURES = {"M0": BASE, "M1": BASE + BEHAVIOR, "M2": BASE + GLU, "M3": BASE + BEHAVIOR + GLU}


def metrics(y, prediction):
    return {"R2": r2_score(y, prediction) if len(y) > 1 and np.var(y) > 0 else np.nan,
            "MAE": mean_absolute_error(y, prediction),
            "RMSE": float(np.sqrt(mean_squared_error(y, prediction)))}


def pipeline(features, algorithm, seed):
    preprocessor = ColumnTransformer([
        ("numeric", StandardScaler(), [c for c in features if c != "condition"]),
        ("condition", OneHotEncoder(drop="first", handle_unknown="ignore", sparse_output=False), ["condition"]),
    ])
    if algorithm == "linear":
        estimator = LinearRegression()
    elif algorithm == "rf":
        estimator = RandomForestRegressor(n_estimators=300, min_samples_leaf=3,
                                          max_features="sqrt", random_state=seed, n_jobs=1)
    else:
        raise ValueError(f"Algoritmo desconocido: {algorithm}")
    return make_pipeline(preprocessor, estimator)


def evaluate(frame, model_names=("M0", "M1", "M2", "M3"), algorithm="linear", n_splits=5, seed=42):
    required = list(dict.fromkeys(["subject_id", "fatigue_future"] + [c for m in model_names for c in FEATURES[m]]))
    sample = frame.dropna(subset=required).sort_values(["subject_id", "condition", "session"]).reset_index(drop=True)
    n_subjects = sample.subject_id.nunique()
    if not 2 <= n_splits <= n_subjects:
        raise ValueError(f"Se requieren 2 <= folds <= sujetos; folds={n_splits}, sujetos completos={n_subjects}")
    numeric = sample[required].select_dtypes(include="number")
    if not np.isfinite(numeric.to_numpy()).all():
        raise ValueError("La muestra contiene valores no finitos")
    splits = list(GroupKFold(n_splits=n_splits).split(sample, groups=sample.subject_id))
    oof = sample[["subject_id", "condition", "session", "fatigue", "fatigue_future", "delta_fatigue"]].copy()
    oof["fold"] = -1
    fold_records, scores = [], []
    y = sample.fatigue_future.to_numpy()
    predictions = {m: np.full(len(sample), np.nan) for m in ["persistence", "train_mean", *model_names]}
    for fold, (train, test) in enumerate(splits):
        if set(sample.subject_id.iloc[train]) & set(sample.subject_id.iloc[test]):
            raise RuntimeError("Fuga de participantes entre entrenamiento y prueba")
        oof.loc[test, "fold"] = fold
        predictions["persistence"][test] = sample.fatigue.iloc[test]
        predictions["train_mean"][test] = y[train].mean()
        for name in model_names:
            features = FEATURES[name]
            model = pipeline(features, algorithm, seed)
            model.fit(sample.iloc[train][features], y[train])
            predictions[name][test] = model.predict(sample.iloc[test][features])
        for name, pred in predictions.items():
            fold_records.append({"model": name, "fold": fold, "n_test": len(test),
                                 "subjects_test": sample.subject_id.iloc[test].nunique(),
                                 **metrics(y[test], pred[test])})
    for name, prediction in predictions.items():
        if not np.isfinite(prediction).all():
            raise RuntimeError("Predicciones OOF incompletas")
        oof[f"pred_{name}"] = prediction
        scores.append({"model": name, "n": len(sample), "subjects": n_subjects, **metrics(y, prediction)})
    scores = pd.DataFrame(scores)
    baseline = scores.set_index("model").loc["M0"] if "M0" in model_names else None
    if baseline is not None:
        scores["delta_R2_vs_M0"] = scores.R2 - baseline.R2
        scores["MAE_improvement_vs_M0"] = baseline.MAE - scores.MAE
    return scores, pd.DataFrame(fold_records), oof


def bootstrap_difference(oof, model="M2", reference="M0", repeats=2000, seed=42):
    """Paired participant bootstrap, conditional on already fitted OOF models."""
    if repeats < 1:
        raise ValueError("repeats debe ser positivo")
    groups = [part for _, part in oof.groupby("subject_id", sort=True)]
    if len(groups) < 2:
        raise ValueError("Se requieren al menos dos participantes")
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(repeats):
        sample = pd.concat([groups[i] for i in rng.integers(0, len(groups), len(groups))], ignore_index=True)
        y = sample.fatigue_future
        a, b = metrics(y, sample[f"pred_{model}"]), metrics(y, sample[f"pred_{reference}"])
        draws.append({"delta_R2": a["R2"] - b["R2"], "MAE_improvement": b["MAE"] - a["MAE"],
                      "RMSE_improvement": b["RMSE"] - a["RMSE"]})
    return pd.DataFrame(draws)


def associations(frame, model_names):
    """Exploratory OLS associations; clustered SEs do not establish prediction."""
    import statsmodels.formula.api as smf
    required = list(dict.fromkeys(["subject_id", "fatigue_future"] + [c for m in model_names for c in FEATURES[m]]))
    sample = frame.dropna(subset=required).copy()
    if sample.subject_id.nunique() < 2:
        raise ValueError("Se requieren al menos dos participantes para errores agrupados")
    output = {}
    for name in model_names:
        terms = ["C(condition)" if c == "condition" else c for c in FEATURES[name]]
        formula = "fatigue_future ~ " + " + ".join(terms)
        fit = smf.ols(formula, sample)
        if np.linalg.matrix_rank(fit.exog) < fit.exog.shape[1] or len(sample) <= fit.exog.shape[1]:
            output[name] = "Modelo no estimable: diseño singular o sin grados de libertad residuales."
            continue
        result = fit.fit(cov_type="cluster", cov_kwds={"groups": sample.subject_id}, use_t=True)
        output[name] = result.summary().as_text()
    return output


def longitudinal_baseline(frame):
    """Random-intercept baseline; explicitly report convergence and warnings."""
    import warnings
    import statsmodels.formula.api as smf
    sample = frame.dropna(subset=["subject_id", "fatigue_future", *BASE]).copy()
    if sample.subject_id.nunique() < 3 or sample.groupby("subject_id").size().max() < 2:
        return "MixedLM no estimable: se requieren sujetos con medidas repetidas."
    formula = "fatigue_future ~ fatigue + session + C(condition)"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            result = smf.mixedlm(formula, sample, groups=sample.subject_id).fit(reml=False, method="powell")
            text = f"Convergencia: {result.converged}\n" + result.summary().as_text()
        except (ValueError, np.linalg.LinAlgError) as error:
            text = f"MixedLM no estimable: {error}"
    return text + "\nAdvertencias:\n" + "\n".join(str(w.message) for w in caught)
