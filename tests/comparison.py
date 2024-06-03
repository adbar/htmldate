"""
Compare extraction results with other libraries of the same kind.
"""

import json

# import logging
import os
import time


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


# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
# list the jsons containing the pages here
eval_paths = ["eval_mediacloud_2020.json", "eval_default.json"]
# load the pages here
EVAL_PAGES = {}
for each in eval_paths:
    evalpath = os.path.join(TEST_DIR, each)
    with open(evalpath, "r", encoding="utf-8") as f:
        EVAL_PAGES.update(json.load(f))


def calculate_scores(name, mydict):
    """output weighted result score"""
    tp, fn, fp, tn = (
        mydict["true_positives"],
        mydict["false_negatives"],
        mydict["false_positives"],
        mydict["true_negatives"],
    )
    time_num1 = mydict["time"] / htmldate_extensive_result["time"]
    time1 = f"{time_num1:.2f}x"
    time_num2 = mydict["time"] / htmldate_fast_result["time"]
    time2 = f"{time_num2:.2f}x"
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    accuracy = (tp + tn) / (tp + tn + fp + fn)
    fscore = (2 * tp) / (2 * tp + fp + fn)  # 2*((precision*recall)/(precision+recall))
    return name, precision, recall, accuracy, fscore, mydict["time"], time1, time2


template_dict = {
    "true_positives": 0,
    "false_positives": 0,
    "true_negatives": 0,
    "false_negatives": 0,
    "time": 0,
}
(
    everything,
    nothing,
    htmldate_extensive_result,
    htmldate_fast_result,
    newspaper_result,
    newsplease_result,
    articledateextractor_result,
    dateguesser_result,
    goose_result,
) = ({}, {}, {}, {}, {}, {}, {}, {}, {})
everything.update(template_dict)
nothing.update(template_dict)
htmldate_extensive_result.update(template_dict)
htmldate_fast_result.update(template_dict)
newspaper_result.update(template_dict)
newsplease_result.update(template_dict)
articledateextractor_result.update(template_dict)
dateguesser_result.update(template_dict)
goose_result.update(template_dict)


i = 0

for item, data in EVAL_PAGES.items():
    i += 1
    # print(item)
    htmlstring = load_document(data["file"])
    # null hypotheses
    tp, fp, tn, fn = evaluate_result(None, data)
    nothing["true_positives"] += tp
    nothing["false_positives"] += fp
    nothing["true_negatives"] += tn
    nothing["false_negatives"] += fn
    # htmldate
    start = time.time()
    result = run_htmldate_extensive(htmlstring)
    htmldate_extensive_result["time"] += time.time() - start
    tp, fp, tn, fn = evaluate_result(result, data)
    htmldate_extensive_result["true_positives"] += tp
    htmldate_extensive_result["false_positives"] += fp
    htmldate_extensive_result["true_negatives"] += tn
    htmldate_extensive_result["false_negatives"] += fn
    # htmldate fast
    start = time.time()
    result = run_htmldate_fast(htmlstring)
    htmldate_fast_result["time"] += time.time() - start
    tp, fp, tn, fn = evaluate_result(result, data)
    htmldate_fast_result["true_positives"] += tp
    htmldate_fast_result["false_positives"] += fp
    htmldate_fast_result["true_negatives"] += tn
    htmldate_fast_result["false_negatives"] += fn
    # newspaper
    start = time.time()
    result = run_newspaper(htmlstring)
    newspaper_result["time"] += time.time() - start
    tp, fp, tn, fn = evaluate_result(result, data)
    newspaper_result["true_positives"] += tp
    newspaper_result["false_positives"] += fp
    newspaper_result["true_negatives"] += tn
    newspaper_result["false_negatives"] += fn
    # newsplease
    start = time.time()
    result = run_newsplease(htmlstring)
    newsplease_result["time"] += time.time() - start
    tp, fp, tn, fn = evaluate_result(result, data)
    newsplease_result["true_positives"] += tp
    newsplease_result["false_positives"] += fp
    newsplease_result["true_negatives"] += tn
    newsplease_result["false_negatives"] += fn
    # articledateextractor
    start = time.time()
    result = run_articledateextractor(htmlstring)
    articledateextractor_result["time"] += time.time() - start
    tp, fp, tn, fn = evaluate_result(result, data)
    articledateextractor_result["true_positives"] += tp
    articledateextractor_result["false_positives"] += fp
    articledateextractor_result["true_negatives"] += tn
    articledateextractor_result["false_negatives"] += fn
    # date_guesser
    start = time.time()
    result = run_dateguesser(htmlstring)
    dateguesser_result["time"] += time.time() - start
    tp, fp, tn, fn = evaluate_result(result, data)
    dateguesser_result["true_positives"] += tp
    dateguesser_result["false_positives"] += fp
    dateguesser_result["true_negatives"] += tn
    dateguesser_result["false_negatives"] += fn
    # goose
    start = time.time()
    result = run_goose(htmlstring)
    goose_result["time"] += time.time() - start
    tp, fp, tn, fn = evaluate_result(result, data)
    goose_result["true_positives"] += tp
    goose_result["false_positives"] += fp
    goose_result["true_negatives"] += tn
    goose_result["false_negatives"] += fn


print("Sample Size:", i)
table = [
    calculate_scores("htmldate extensive", htmldate_extensive_result),
    calculate_scores("htmldate fast", htmldate_fast_result),
    calculate_scores("newspaper", newspaper_result),
    calculate_scores("newsplease", newsplease_result),
    calculate_scores("articledateextractor", articledateextractor_result),
    calculate_scores("date_guesser", dateguesser_result),
    calculate_scores("goose", goose_result),
]
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
        floatfmt=[".3f", ".3f", ".3f", ".3f", ".3f", ".3f"],
    )
)


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
            floatfmt=[".3f", ".3f", ".3f", ".3f", ".3f", ".3f"],
        ),
        file=f,
    )
print("Results also saved as comparison_results.txt")
