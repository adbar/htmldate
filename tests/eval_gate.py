"""CI quality gate: fail if the benchmark F1-score regresses below baseline.

Run from the tests directory. Pin ``TZ=Europe/Berlin`` to reproduce the
baseline (F1 depends on local time and the dateparser/lxml versions).
"""

import sys

from evaluation import (
    EVAL_PAGES,
    evaluate_result,
    f1_score,
    load_document,
    run_htmldate_extensive,
    run_htmldate_fast,
)

# current full-corpus baseline; no regression allowed
FLOORS = {"extensive": 0.9490, "fast": 0.9253}
RUNNERS = {"extensive": run_htmldate_extensive, "fast": run_htmldate_fast}


def score_function(func):
    tp = fp = fn = 0
    for _, data in EVAL_PAGES.items():
        true_pos, false_pos, _, false_neg = evaluate_result(
            func(load_document(data["file"])), data
        )
        tp, fp, fn = tp + true_pos, fp + false_pos, fn + false_neg
    return f1_score(tp, fp, fn)


def main():
    regression = False
    for name, func in RUNNERS.items():
        score, floor = round(score_function(func), 4), FLOORS[name]
        regression = regression or score < floor
        print(f"{name:>9}: F1={score:.4f} (floor {floor:.4f})")
    return int(regression)


if __name__ == "__main__":
    sys.exit(main())
