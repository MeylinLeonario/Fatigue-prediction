"""Versioned source files, integrity checks and explicit schema validation."""
import hashlib
from pathlib import Path
from urllib.request import urlopen

import numpy as np
import pandas as pd

RECORD = "https://zenodo.org/records/6795446"
# Published MD5 values identify the source bytes, not a security guarantee.
FILES = {
    "ratings": ("MRSFATIGUE_ratings_session_zenodo.csv", "f1c71b359e4a2f4e7cbb6f947141d7f6"),
    "ntask": ("MRSFATIGUE_ntask_session_zenodo.csv", "fb2713df6649d2aba07358f3794fb570"),
    "glu": ("MRSFATIGUE_MRS_semiLaser_session_ratio_Glu_tCr_zenodo.csv", "3d86698059b9f6b4dcae8f4fb07ec8c3"),
    "dws": ("MRSFATIGUE_MRS_DWS_session_ADC_log_Glu_Gln_lin_zenodo.csv", "b657b25c2ba74b92080a5c78b0133577"),
    "choice": ("MRSFATIGUE_choice_bias_parameter_zenodo.csv", "36d3279abed47a31edb0c7e79ebef874"),
    "pupil": ("MRSFATIGUE_pupil_choice_session_zenodo.csv", "16cc89dffa56d78d4c6a171c1cf35e98"),
}
KEYS = ["subject_id", "condition", "session"]
SCHEMAS = {
    "ratings": ["question", "rating"],
    "ntask": ["task", "block", "trial", "performance", "response_time", "rule_switch"],
    "glu": ["ROI", "Glu_tCr"],
    "dws": ["ROI", "ADC_log_Glu_Gln_lin"],
}


def checksum(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "md5").hexdigest()


def download(directory, include_all=False):
    """Download atomically; never silently replace a corrupted existing file."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for name in (FILES if include_all else SCHEMAS):
        filename, expected = FILES[name]
        target = directory / filename
        if target.exists():
            if checksum(target) != expected:
                raise ValueError(f"Checksum incorrecto: {target}; revise el archivo antes de eliminarlo")
            continue
        temporary = target.with_suffix(".csv.part")
        try:
            with urlopen(f"{RECORD}/files/{filename}?download=1", timeout=120) as src, temporary.open("wb") as dst:
                while chunk := src.read(1024 * 1024):
                    dst.write(chunk)
            if checksum(temporary) != expected:
                raise ValueError(f"Checksum incorrecto en descarga: {filename}")
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)


def validate(frame, name):
    missing = set(KEYS + SCHEMAS[name]) - set(frame.columns)
    if missing:
        raise ValueError(f"{name}: faltan columnas {sorted(missing)}")
    frame = frame.copy()
    if frame[KEYS].isna().any().any():
        raise ValueError(f"{name}: identificadores ausentes")
    frame["session"] = pd.to_numeric(frame["session"], errors="raise")
    if not np.isfinite(frame.session).all() or (frame.session % 1 != 0).any():
        raise ValueError(f"{name}: sesiones deben ser enteros finitos")
    numeric = {"ratings": ["rating"], "ntask": ["block", "trial", "performance", "response_time", "rule_switch"],
               "glu": ["Glu_tCr"], "dws": ["ADC_log_Glu_Gln_lin"]}[name]
    for col in numeric:
        frame[col] = pd.to_numeric(frame[col], errors="raise")
        if np.isinf(frame[col].to_numpy(dtype=float)).any():
            raise ValueError(f"{name}: infinito en {col}")
    for col in (["performance", "rule_switch"] if name == "ntask" else []):
        if not frame[col].dropna().isin([0, 1]).all():
            raise ValueError(f"{name}: {col} debe ser binaria")
    if name == "ratings" and not frame.rating.dropna().between(0, 100).all():
        raise ValueError("ratings: escala esperada 0–100")
    return frame


def load(directory):
    result, provenance = {}, {}
    for name in SCHEMAS:
        filename, expected = FILES[name]
        path = Path(directory) / filename
        if not path.exists():
            raise FileNotFoundError(f"Falta {path}. Ejecute python -m fatigue_prediction download --data-dir {directory}")
        digest = checksum(path)
        if digest != expected:
            raise ValueError(f"Checksum incorrecto: {path}")
        result[name] = validate(pd.read_csv(path), name)
        provenance[name] = {"file": filename, "md5": digest, "rows": len(result[name])}
    return result, provenance
