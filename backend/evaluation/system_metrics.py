"""Shared benchmarking framework for DietRiskNet evaluation.

Provides:
- timing / statistics (mean, median, p95) via ``StatsCollector``
- memory and CPU helpers (``tracemalloc`` + optional ``psutil``)
- CSV / JSON report writers
- matplotlib chart generation
- dissertation-ready thesis tables (Table 5.1, 5.2, ...)
- a ``run_all`` convenience that executes every benchmark
"""

from __future__ import annotations

import csv
import json
import os
import statistics
import time
import tracemalloc
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Default output directory for all reports / charts / tables.
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "reports")


# ----------------------------------------------------------------------
# Statistics
# ----------------------------------------------------------------------

def _pct(sorted_samples: List[float], pct: float) -> float:
    if not sorted_samples:
        return 0.0
    idx = min(len(sorted_samples) - 1, int(round(pct / 100.0 * (len(sorted_samples) - 1))))
    return sorted_samples[idx]


@dataclass
class MetricSample:
    """Timing samples for one metric."""

    name: str
    samples_ms: List[float] = field(default_factory=list)

    def add(self, ms: float) -> None:
        self.samples_ms.append(ms)

    @property
    def count(self) -> int:
        return len(self.samples_ms)

    @property
    def mean_ms(self) -> float:
        return statistics.fmean(self.samples_ms) if self.samples_ms else 0.0

    @property
    def median_ms(self) -> float:
        return statistics.median(self.samples_ms) if self.samples_ms else 0.0

    @property
    def p95_ms(self) -> float:
        return _pct(sorted(self.samples_ms), 95.0)

    def summary(self) -> Dict[str, float]:
        return {
            "count": self.count,
            "mean_ms": round(self.mean_ms, 3),
            "median_ms": round(self.median_ms, 3),
            "p95_ms": round(self.p95_ms, 3),
        }


class StatsCollector:
    """Accumulates timing samples and computes summary statistics."""

    def __init__(self) -> None:
        self._metrics: Dict[str, MetricSample] = {}

    def sample(self, name: str, elapsed_ms: float) -> None:
        metric = self._metrics.setdefault(name, MetricSample(name))
        metric.add(elapsed_ms)

    def metric(self, name: str) -> MetricSample:
        return self._metrics.setdefault(name, MetricSample(name))

    def summary(self) -> Dict[str, Dict[str, float]]:
        return {name: m.summary() for name, m in self._metrics.items()}


@contextmanager
def timer(collector: StatsCollector, name: str):
    """Time a block and record elapsed milliseconds into *collector*."""
    start = time.perf_counter()
    try:
        yield
    finally:
        collector.sample(name, (time.perf_counter() - start) * 1000.0)


# ----------------------------------------------------------------------
# Memory / CPU
# ----------------------------------------------------------------------

def start_memory_tracking() -> None:
    tracemalloc.start()


def stop_memory_tracking() -> Dict[str, float]:
    """Return current + peak traced memory in MB."""
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "current_mb": round(current / (1024 * 1024), 3),
        "peak_mb": round(peak / (1024 * 1024), 3),
    }


def cpu_percent(interval: float = 0.1) -> Optional[float]:
    """Return CPU utilisation percent, or None if psutil is unavailable."""
    try:
        import psutil
        return psutil.cpu_percent(interval=interval)
    except Exception:
        return None


def current_rss_mb() -> float:
    """Return current process resident-set memory in MB (best effort)."""
    try:
        import psutil
        return round(psutil.Process().memory_info().rss / (1024 * 1024), 3)
    except Exception:
        return 0.0


# ----------------------------------------------------------------------
# Report writers
# ----------------------------------------------------------------------

def write_csv(path: str, header: List[str], rows: List[List[Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ----------------------------------------------------------------------
# Charts
# ----------------------------------------------------------------------

def _use_agg() -> None:
    import matplotlib
    matplotlib.use("Agg")


def _styled_bar(ax, labels, values, title, ylabel, color="#2563EB") -> None:
    bars = ax.barh(labels, values, color=color)
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_width(), bar.get_y() + bar.get_height() / 2.0,
            f"{val:.2f}", va="center", ha="left", fontsize=8,
        )
    ax.set_title(title, fontsize=12)
    ax.set_xlabel(ylabel, fontsize=9)
    ax.invert_yaxis()
    ax.grid(axis="x", linestyle="--", alpha=0.4)


def generate_charts(all_results: Dict[str, Any], output_dir: str = DEFAULT_OUTPUT_DIR) -> List[str]:
    """Create PNG charts for pipeline, cache, AI, memory, and PDF metrics.

    Returns the list of generated chart file paths.
    """
    _use_agg()
    import matplotlib.pyplot as plt

    os.makedirs(output_dir, exist_ok=True)
    generated: List[str] = []

    # 1. Pipeline latency
    pipeline = all_results.get("pipeline", {}).get("metrics", {})
    if pipeline:
        labels = [k for k in pipeline.keys()]
        means = [v["mean_ms"] for v in pipeline.values()]
        fig, ax = plt.subplots(figsize=(7, 4.5))
        _styled_bar(ax, labels, means, "Pipeline Stage Latency (mean, ms)", "Stage")
        fig.tight_layout()
        path = os.path.join(output_dir, "pipeline_latency.png")
        fig.savefig(path, dpi=120)
        plt.close(fig)
        generated.append(path)

    # 2. Cache performance (hit vs miss)
    cache = all_results.get("cache", {}).get("metrics", {})
    hit = cache.get("cache_hit", {}).get("mean_ms")
    miss = cache.get("cache_miss", {}).get("mean_ms")
    if hit is not None and miss is not None:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.bar(["Cache Hit", "Cache Miss"], [hit, miss],
               color=["#10B981", "#F59E0B"])
        for i, v in enumerate([hit, miss]):
            ax.text(i, v, f"{v:.2f} ms", ha="center", va="bottom", fontsize=9)
        ax.set_title("Cache Performance (mean latency, ms)")
        ax.set_ylabel("Latency (ms)")
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        fig.tight_layout()
        path = os.path.join(output_dir, "cache_performance.png")
        fig.savefig(path, dpi=120)
        plt.close(fig)
        generated.append(path)

    # 3. AI latency
    ai = all_results.get("ai", {}).get("metrics", {})
    ai_miss = ai.get("ai_cache_miss", {}).get("mean_ms")
    ai_hit = ai.get("ai_cache_hit", {}).get("mean_ms")
    if ai_miss is not None or ai_hit is not None:
        labels, values = [], []
        if ai_hit is not None:
            labels.append("AI Cache Hit"); values.append(ai_hit)
        if ai_miss is not None:
            labels.append("AI Cache Miss"); values.append(ai_miss)
        fig, ax = plt.subplots(figsize=(6, 3.5))
        _styled_bar(ax, labels, values, "AI Dietitian Latency (mean, ms)", "Path")
        fig.tight_layout()
        path = os.path.join(output_dir, "ai_latency.png")
        fig.savefig(path, dpi=120)
        plt.close(fig)
        generated.append(path)

    # 4. Memory usage
    memory = all_results.get("system", {}).get("memory", {})
    if memory:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        labels = [k for k in memory.keys()]
        values = [float(v) for v in memory.values()]
        _styled_bar(ax, labels, values, "Memory Usage (MB)", "Metric")
        fig.tight_layout()
        path = os.path.join(output_dir, "memory_usage.png")
        fig.savefig(path, dpi=120)
        plt.close(fig)
        generated.append(path)

    # 5. PDF generation
    pdf = all_results.get("pdf", {}).get("metrics", {})
    pdf_time = pdf.get("pdf_generation", {}).get("mean_ms")
    if pdf_time is not None:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.bar(["PDF Generation"], [pdf_time], color="#8B5CF6")
        ax.text(0, pdf_time, f"{pdf_time:.2f} ms", ha="center", va="bottom", fontsize=9)
        ax.set_title("PDF Generation Time (mean, ms)")
        ax.set_ylabel("Time (ms)")
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        fig.tight_layout()
        path = os.path.join(output_dir, "pdf_generation.png")
        fig.savefig(path, dpi=120)
        plt.close(fig)
        generated.append(path)

    return generated


# ----------------------------------------------------------------------
# Thesis tables (markdown)
# ----------------------------------------------------------------------

def _md_table(header: List[str], rows: List[List[Any]]) -> str:
    lines = ["| " + " | ".join(str(h) for h in header) + " |"]
    lines.append("|" + "|".join(["---"] * len(header)) + "|")
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def generate_thesis_tables(all_results: Dict[str, Any], output_dir: str = DEFAULT_OUTPUT_DIR) -> List[str]:
    """Write markdown tables suitable for insertion into the dissertation.

    Returns the list of generated table file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    generated: List[str] = []

    # Table 5.1 - Pipeline Runtime
    pipeline = all_results.get("pipeline", {}).get("metrics", {})
    if pipeline:
        header = ["Stage", "Mean (ms)", "Median (ms)", "P95 (ms)"]
        rows = [
            [name, v["mean_ms"], v["median_ms"], v["p95_ms"]]
            for name, v in pipeline.items()
        ]
        total = sum(v["mean_ms"] for v in pipeline.values())
        rows.append(["Total (pipeline stages)", round(total, 3), "", ""])
        text = "**Table 5.1 - Pipeline Runtime**\n\n" + _md_table(header, rows)
        path = os.path.join(output_dir, "table_5_1_pipeline_runtime.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        generated.append(path)

    # Table 5.2 - Cache Performance.
    # The end-to-end benefit is measured with the AI latencies (a cache
    # miss includes the LLM call); the micro-benchmark hit/miss is used
    # only as a fallback.
    cache = all_results.get("cache", {})
    cache_metrics = cache.get("metrics", {})
    ai_metrics = all_results.get("ai", {}).get("metrics", {})
    hit = (
        ai_metrics.get("ai_cache_hit", {}).get("mean_ms")
        or cache_metrics.get("cache_hit", {}).get("mean_ms")
    )
    miss = (
        ai_metrics.get("ai_cache_miss", {}).get("mean_ms")
        or cache_metrics.get("cache_miss", {}).get("mean_ms")
    )
    hit_rate = cache.get("hit_rate")
    if hit is not None or miss is not None:
        improvement = (
            (1.0 - hit / miss) * 100.0 if hit is not None and miss and miss > 0 else 0.0
        )
        header = ["Metric", "Value"]
        rows = [
            ["Cache hit rate", f"{hit_rate:.2%}" if hit_rate is not None else "N/A"],
            ["Average cache hit latency (ms)", f"{hit:.3f}" if hit is not None else "N/A"],
            ["Average cache miss latency (ms)", f"{miss:.3f}" if miss is not None else "N/A"],
            ["Latency improvement (hit vs miss)", f"{improvement:.2f}%"],
        ]
        text = "**Table 5.2 - Cache Performance**\n\n" + _md_table(header, rows)
        path = os.path.join(output_dir, "table_5_2_cache_performance.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        generated.append(path)

    # Table 5.3 — AI Dietitian latency
    ai = all_results.get("ai", {}).get("metrics", {})
    if ai:
        header = ["Path", "Mean (ms)", "Median (ms)", "P95 (ms)"]
        rows = [
            [name, v["mean_ms"], v["median_ms"], v["p95_ms"]]
            for name, v in ai.items()
        ]
        text = "**Table 5.3 - AI Dietitian Latency**\n\n" + _md_table(header, rows)
        path = os.path.join(output_dir, "table_5_3_ai_latency.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        generated.append(path)

    # Table 5.4 — PDF generation
    pdf = all_results.get("pdf", {})
    pdf_metrics = pdf.get("metrics", {})
    if pdf_metrics:
        header = ["Metric", "Mean (ms)", "Median (ms)", "P95 (ms)", "Size (bytes)"]
        rows = [
            [
                "PDF generation",
                pdf_metrics.get("pdf_generation", {}).get("mean_ms", "N/A"),
                pdf_metrics.get("pdf_generation", {}).get("median_ms", "N/A"),
                pdf_metrics.get("pdf_generation", {}).get("p95_ms", "N/A"),
                pdf.get("avg_pdf_size_bytes", "N/A"),
            ]
        ]
        text = "**Table 5.4 - PDF Generation**\n\n" + _md_table(header, rows)
        path = os.path.join(output_dir, "table_5_4_pdf_generation.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        generated.append(path)

    return generated


# ----------------------------------------------------------------------
# Convenience runner
# ----------------------------------------------------------------------

def run_all(output_dir: str = DEFAULT_OUTPUT_DIR, iterations: int = 3) -> Dict[str, Any]:
    """Run every benchmark and produce CSV, JSON, charts, and tables."""
    from backend.evaluation.benchmark_ai import run_benchmark as run_ai
    from backend.evaluation.benchmark_cache import run_benchmark as run_cache
    from backend.evaluation.benchmark_pdf import run_benchmark as run_pdf
    from backend.evaluation.benchmark_pipeline import run_benchmark as run_pipeline

    all_results: Dict[str, Any] = {}

    pipeline = run_pipeline(output_dir=output_dir, iterations=iterations)
    all_results["pipeline"] = pipeline

    cache = run_cache(output_dir=output_dir, iterations=iterations)
    all_results["cache"] = cache

    ai = run_ai(output_dir=output_dir, iterations=iterations)
    all_results["ai"] = ai

    pdf = run_pdf(output_dir=output_dir, iterations=iterations)
    all_results["pdf"] = pdf

    # System-level summary
    all_results["system"] = {
        "memory": _measure_system_memory(),
        "cpu_percent": cpu_percent(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
    }

    # Aggregate report
    write_json(os.path.join(output_dir, "system_metrics.json"), all_results)

    # Charts + thesis tables
    generate_charts(all_results, output_dir)
    generate_thesis_tables(all_results, output_dir)

    return all_results


def _measure_system_memory() -> Dict[str, float]:
    start_memory_tracking()
    # Trigger a small allocation so tracemalloc captures some activity.
    _scratch = [i for i in range(10000)]
    del _scratch
    memory = stop_memory_tracking()
    memory["rss_mb"] = current_rss_mb()
    return memory


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run all DietRiskNet benchmarks")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--iterations", type=int, default=3)
    args = parser.parse_args()
    run_all(output_dir=args.output_dir, iterations=args.iterations)
    print(f"Benchmarks complete. Reports written to {args.output_dir}")
