"""
Compare extraction results with other libraries of the same kind.
"""

import argparse
import contextlib
import json
import os
import sys
import time

import tqdm

from tabulate import tabulate


from evaluation import (
    evaluate_result,
    load_document,
    run_htmldate_extensive,
    run_htmldate_fast,
    run_articledateextractor,
    run_dateguesser,
    run_newspaper,
    run_newsplease,
    run_goose,
)


TEST_DIR = os.path.abspath(os.path.dirname(__file__))
# list the jsons containing the pages here
eval_paths = ["eval_mediacloud_2020.json", "eval_default.json"]
# load the pages here
EVAL_PAGES = {}
for each in eval_paths:
    evalpath = os.path.join(TEST_DIR, each)
    with open(evalpath, "r", encoding="utf-8") as f:
        EVAL_PAGES.update(json.load(f))


PARSER = argparse.ArgumentParser(description="Run the evaluation")
PARSER.add_argument(
    "--small",
    action="store_true",
    help="Only take htmldate into account",
)
PARSER.add_argument(
    "--verbose",
    action="store_true",
    help="Increase verbosity",
)
ARGS = PARSER.parse_args()


TEMPLATE_DICT = {
    "true_positives": 0,
    "false_positives": 0,
    "true_negatives": 0,
    "false_negatives": 0,
    "time": 0,
}

FUNC_DICT = {
    "htmldate_extensive": run_htmldate_extensive,
    "htmldate_fast": run_htmldate_fast,
    **{
        key: func
        for key, func in [
            ("newspaper", run_newspaper),
            ("newsplease", run_newsplease),
            ("articledateextractor", run_articledateextractor),
            ("date_guesser", run_dateguesser),
            ("goose", run_goose),
        ]
        if not ARGS.small
    },
}

RESULTS_DICT = {key: TEMPLATE_DICT.copy() for key, value in FUNC_DICT.items()}


def calculate_scores(name, mydict):
    "Output weighted result score."
    tp, fn, fp, tn = (
        mydict["true_positives"],
        mydict["false_negatives"],
        mydict["false_positives"],
        mydict["true_negatives"],
    )
    time1 = f'{mydict["time"] / RESULTS_DICT["htmldate_extensive"]["time"] :.2f}x'
    time2 = f'{mydict["time"] / RESULTS_DICT["htmldate_fast"]["time"] :.2f}x'
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    accuracy = (tp + tn) / (tp + tn + fp + fn)
    fscore = (2 * tp) / (2 * tp + fp + fn)  # 2*((precision*recall)/(precision+recall))
    return name, precision, recall, accuracy, fscore, mydict["time"], time1, time2


def run_eval(html, data):
    "Run the evaluation with each function in the benchmark."
    for function_name, func in FUNC_DICT.items():
        start = time.time()
        result = func(html)
        RESULTS_DICT[function_name]["time"] += time.time() - start

        tp, fp, tn, fn = evaluate_result(result, data)
        RESULTS_DICT[function_name]["true_positives"] += tp
        RESULTS_DICT[function_name]["false_positives"] += fp
        RESULTS_DICT[function_name]["true_negatives"] += tn
        RESULTS_DICT[function_name]["false_negatives"] += fn


if __name__ == "__main__":

    # hack to suppress noise
    my_stdout = sys.stdout if ARGS.verbose else None
    my_stderr = sys.stderr if ARGS.verbose else None

    for item, data in tqdm.tqdm(EVAL_PAGES.items(), total=len(EVAL_PAGES)):
        htmlstring = load_document(data["file"])
        with contextlib.redirect_stdout(my_stdout), contextlib.redirect_stderr(
            my_stderr
        ):
            run_eval(htmlstring, data)

    table = [calculate_scores(key, value) for key, value in RESULTS_DICT.items()]

    print()
    print(
        tabulate(
            table,
            headers=["Name", "Prec.", "Rec.", "Acc.", "F1", "Time", "x ext.", "x fast"],
            floatfmt=[".3f", ".3f", ".3f", ".3f", ".3f", ".2f"],
        )
    )
    print()

    with open("comparison_results.txt", "w", encoding="utf-8") as f:
        print(
            tabulate(
                table,
                headers=[
                    "Name",
                    "Precision",
                    "Recall",
                    "Accuracy",
                    "F-score",
                    "Time (s)",
                    "Time (Relative to htmldate extensive)",
                    "Time (Relative to htmldate fast)",
                ],
                floatfmt=[".3f", ".3f", ".3f", ".3f", ".3f", ".2f"],
            ),
            file=f,
        )

    print("Results also saved as comparison_results.txt")
