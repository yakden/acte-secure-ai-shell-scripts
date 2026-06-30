"""ACTE experiment harness.

Modules
-------
* dataset           -- load the manifest and produce deterministic splits
* metrics           -- precision/recall/F1/MCC/accuracy/confusion matrix
* figures           -- ROC and Precision-Recall curve rendering
* acte_eval         -- train + evaluate ACTE and run the ablation study
* baseline_shellcheck -- run ShellCheck as a baseline detector
* latency           -- per-script analysis-latency measurement (RQ2)
* run_all           -- single deterministic entrypoint for the whole study
"""
