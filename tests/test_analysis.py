"""Regression tests for temporal integrity and participant-isolated evaluation."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from fatigue_prediction.data import FILES, checksum, download, validate
from fatigue_prediction.features import behavior, build, spectroscopy, transitions
from fatigue_prediction.models import BASE, bootstrap_difference, evaluate, pipeline
from fatigue_prediction.cli import run


def fixtures():
    ratings, trials, glu, dws = [], [], [], []
    rng = np.random.default_rng(4)
    for subject in range(12):
        condition = "hard" if subject % 2 else "easy"
        for session in range(4):
            key = dict(subject_id=subject, condition=condition, session=session)
            ratings.append(dict(**key, question="Fatigue", rating=20 + subject + 3 * session + rng.normal()))
            for trial in range(8):
                trials.append(dict(**key, task="nback", block=1, trial=trial, performance=float(trial % 3 != 0),
                                   response_time=.4 + .02 * trial + .01 * session, rule_switch=float(trial % 2)))
            for roi in ["PFC", "VC"]:
                glu.append(dict(**key, ROI=roi, Glu_tCr=1 + .03 * subject + .02 * session))
                dws.append(dict(**key, ROI=roi, ADC_log_Glu_Gln_lin=.2 + .001 * subject))
    return {"ratings": pd.DataFrame(ratings), "ntask": pd.DataFrame(trials),
            "glu": pd.DataFrame(glu), "dws": pd.DataFrame(dws)}


class TemporalTests(unittest.TestCase):
    def test_duplicates_excluded_without_bridging(self):
        data = fixtures()["ratings"].query("subject_id == 0")
        data = pd.concat([data, data.query("session == 1")])
        pairs, excluded, audit = transitions(data)
        self.assertEqual(pairs.session.tolist(), [2])
        self.assertEqual(len(excluded), 2)
        self.assertEqual(audit["ambiguous_rows"], 2)

    def test_no_cross_condition_pairs(self):
        data = fixtures()["ratings"].query("subject_id == 0").copy()
        data.loc[data.session.ge(2), "condition"] = "hard"
        paired, _, _ = transitions(data.sample(frac=1, random_state=2))
        self.assertEqual(paired.session.tolist(), [0, 2])
        self.assertTrue((paired.session_future - paired.session).eq(1).all())

    def test_missing_rating_does_not_bridge(self):
        data = fixtures()["ratings"].query("subject_id == 0").copy()
        data.loc[data.session.eq(1), "rating"] = np.nan
        paired, _, _ = transitions(data)
        self.assertEqual(paired.session.tolist(), [2])

    def test_order_and_half_definition(self):
        data = fixtures()["ntask"].query("subject_id == 0 and session == 0")
        features = behavior(data.sample(frac=1, random_state=3)).iloc[0]
        self.assertAlmostEqual(features.within_session_rt_change, .08)
        self.assertEqual(features.n_trials, 8)

    def test_ambiguous_task_order_rejected(self):
        data = fixtures()["ntask"].iloc[:2]
        with self.assertRaisesRegex(ValueError, "ambiguo"):
            behavior(pd.concat([data, data.assign(task="nswitch")]))

    def test_invalid_rt_missing_without_dropping_trial(self):
        data = fixtures()["ntask"].iloc[:8].copy()
        data.loc[0, "response_time"] = -1
        features = behavior(data).iloc[0]
        self.assertEqual(features.n_valid_rt, 7)
        self.assertEqual(features.n_trials, 8)

    def test_duplicate_roi_rejected(self):
        data = fixtures()["glu"].iloc[:2]
        with self.assertRaisesRegex(ValueError, "duplicada"):
            spectroscopy(pd.concat([data, data]), "glu", "Glu_tCr", "Glu")

    def test_bad_schema_and_nonbinary_rejected(self):
        with self.assertRaisesRegex(ValueError, "faltan"):
            validate(pd.DataFrame(), "ratings")
        data = fixtures()["ntask"]
        data.loc[0, "performance"] = 2
        with self.assertRaisesRegex(ValueError, "binaria"):
            behavior(data)


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.frame, _, _ = build(fixtures())

    def test_subjects_isolated_and_common_sample(self):
        self.frame.loc[0, "MRS_Glu_tCr_PFC"] = np.nan
        scores, folds, oof = evaluate(self.frame, n_splits=3)
        self.assertEqual(oof.groupby("subject_id").fold.nunique().max(), 1)
        self.assertTrue(scores.n.eq(len(self.frame) - 1).all())
        self.assertFalse(oof.filter(like="pred_").isna().any().any())
        np.testing.assert_allclose(oof.pred_persistence, oof.fatigue)
        for fold in oof.fold.unique():
            train_mean = oof.loc[oof.fold.ne(fold), "fatigue_future"].mean()
            np.testing.assert_allclose(oof.loc[oof.fold.eq(fold), "pred_train_mean"], train_mean)
        self.assertEqual(len(folds), 18)

    def test_preprocessing_uses_training_only(self):
        model = pipeline(BASE, "linear", 42)
        sample = self.frame.iloc[:9]
        model.fit(sample[BASE], sample.fatigue_future)
        scaler = model.steps[0][1].named_transformers_["numeric"]
        np.testing.assert_allclose(scaler.mean_, sample[["fatigue", "session"]].mean())

    def test_deterministic_and_invalid_folds(self):
        a = evaluate(self.frame, n_splits=3)[2]
        b = evaluate(self.frame, n_splits=3)[2]
        pd.testing.assert_frame_equal(a, b)
        with self.assertRaisesRegex(ValueError, "folds"):
            evaluate(self.frame, n_splits=20)

    def test_bootstrap_is_paired_and_deterministic(self):
        oof = evaluate(self.frame, n_splits=3)[2]
        oof["pred_M2"] = oof.pred_M0
        draws = bootstrap_difference(oof, repeats=20)
        np.testing.assert_allclose(draws, 0)
        pd.testing.assert_frame_equal(draws, bootstrap_difference(oof, repeats=20))

    def test_rf_smoke(self):
        scores, _, oof = evaluate(self.frame, ("M0", "M1"), "rf", n_splits=2)
        self.assertEqual(len(scores), 4)
        self.assertTrue(np.isfinite(oof.pred_M1).all())

    def test_run_exports_and_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("fatigue_prediction.cli.load", return_value=(fixtures(), {"synthetic": True})):
                _, comparison, audit = run("unused", directory, folds=3, bootstrap=10)
            self.assertEqual(len(comparison), 10)
            self.assertTrue((Path(directory) / "audit.json").exists())
            self.assertEqual(audit["valid_transitions"], 36)


class DownloadTests(unittest.TestCase):
    def test_corrupt_file_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / FILES["ratings"][0]
            target.write_text("corrupt")
            with self.assertRaisesRegex(ValueError, "Checksum"):
                download(directory)
            self.assertEqual(target.read_text(), "corrupt")

    def test_streamed_download_checksum_and_partial_cleanup(self):
        import io
        import hashlib
        content = b"a,b\n1,2\n"
        with tempfile.TemporaryDirectory() as directory:
            with patch("fatigue_prediction.data.SCHEMAS", {"ratings": []}), patch.dict(
                FILES, {"ratings": ("test.csv", hashlib.md5(content).hexdigest())}
            ), patch("fatigue_prediction.data.urlopen", return_value=io.BytesIO(content)):
                download(directory)
                self.assertEqual(checksum(Path(directory) / "test.csv"), hashlib.md5(content).hexdigest())
            self.assertFalse(list(Path(directory).glob("*.part")))


if __name__ == "__main__":
    unittest.main()
