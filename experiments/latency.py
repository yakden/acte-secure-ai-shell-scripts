"""Per-script analysis-latency measurement (RQ2).

Measures wall-clock time for a full ACTE analysis (parse -> context ->
threat-intel -> trust -> policy) per script, using a trained engine. Reports
mean, median, p95, p99, min and max in milliseconds, plus throughput. A short
warm-up pass is run first so the bashlex import / regex compilation cost is not
charged to the first measured sample.
"""

from __future__ import annotations

import statistics
import time
from typing import Dict, List

from acte.pipeline import ACTEPipeline
from acte.trust_engine import TrustEvaluationEngine
from experiments.dataset import Sample


def measure_latency(
    samples: List[Sample],
    engine: TrustEvaluationEngine = None,
    repeats: int = 3,
    warmup: int = 5,
) -> Dict:
    """Measure analysis latency per script, averaged over ``repeats`` passes."""
    pipeline = ACTEPipeline(engine=engine or TrustEvaluationEngine())

    # Warm-up so first-call import/compile costs don't skew the numbers.
    for s in samples[:warmup]:
        pipeline.analyze(s.script)

    per_script_ms: List[float] = []
    for s in samples:
        timings = []
        for _ in range(repeats):
            start = time.perf_counter()
            pipeline.analyze(s.script, generate_policy=True)
            timings.append((time.perf_counter() - start) * 1000.0)
        per_script_ms.append(min(timings))  # min reduces scheduler noise

    per_script_ms_sorted = sorted(per_script_ms)
    n = len(per_script_ms_sorted)

    def pct(p: float) -> float:
        if n == 0:
            return 0.0
        idx = min(n - 1, int(round(p / 100.0 * (n - 1))))
        return per_script_ms_sorted[idx]

    mean_ms = statistics.fmean(per_script_ms) if per_script_ms else 0.0
    return {
        "n_scripts": n,
        "repeats_per_script": repeats,
        "mean_ms": mean_ms,
        "median_ms": statistics.median(per_script_ms) if per_script_ms else 0.0,
        "p95_ms": pct(95),
        "p99_ms": pct(99),
        "min_ms": min(per_script_ms) if per_script_ms else 0.0,
        "max_ms": max(per_script_ms) if per_script_ms else 0.0,
        "stdev_ms": statistics.pstdev(per_script_ms) if n > 1 else 0.0,
        "throughput_scripts_per_sec": (1000.0 / mean_ms) if mean_ms else 0.0,
    }
