import numpy as np
import pandas as pd

from scripts.score_benchmark_similarity import regression_report


def test_regression_uses_global_out_of_fold_r2() -> None:
    feature = np.linspace(-3.0, 3.0, 24)
    wide = pd.DataFrame(
        {
            "existing_a": feature,
            "existing_b": feature**2,
            "target": 4.0 * feature - 2.0,
        },
        index=[f"model-{index:02d}" for index in range(len(feature))],
    )

    report = regression_report(wide, "target", min_models=12)

    assert report["status"] == "ok"
    assert report["models"] == 24
    assert report["features"] == 2
    assert float(report["cv_r2"]) > 0.95
    assert float(report["predictive_novelty"]) < 0.05
