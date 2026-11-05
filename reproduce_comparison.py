"""New seeded paired comparisons; never a reconstruction of historical Table 1."""

from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import random
import subprocess
import sys
import tempfile

import numpy as np
from evidence_validation import (
    METHODS, PROTOCOL, encoded, validate_matrix, validate_parameters, validate_results,
    verify_sources,
)
from utils import (
    ant_colony_optimization,
    generate_random_graphs,
    improved_aco_active_inference,
    nearest_neighbor_tsp,
)


def run_comparison(nodes, graphs, seed, ants, iterations):
    parameters = validate_parameters(dict(nodes=nodes, graphs=graphs, seed=seed, ants=ants, iterations=iterations))
    inputs = []
    rows = []
    methods = {
        "nearest_neighbor": nearest_neighbor_tsp,
        "basic_aco": ant_colony_optimization,
        "ai_labelled_elitist_aco": improved_aco_active_inference,
    }
    for n in nodes:
        for i in range(graphs):
            graph_seed = (seed + n * 100003 + i * 101) % (2**32)
            np.random.seed(graph_seed)
            random.seed(graph_seed)
            matrix = np.asarray(generate_random_graphs(1, n)[0], dtype="<f8")
            graph_hash = validate_matrix(matrix.tolist(), n)
            graph_id = f"n{n}-g{i:04d}"
            inputs.append(
                {
                    "graph_id": graph_id,
                    "nodes": n,
                    "seed": graph_seed,
                    "matrix": matrix.tolist(),
                    "matrix_f64le_sha256": graph_hash,
                }
            )
            for method_index, (label, method) in enumerate(methods.items()):
                method_seed = (graph_seed + method_index * 1000003) % (2**32)
                np.random.seed(method_seed)
                random.seed(method_seed)
                kwargs = (
                    {}
                    if label == "nearest_neighbor"
                    else {"num_ants": ants, "num_iterations": iterations}
                )
                tour, length = method(matrix, **kwargs)
                tour = [int(v) for v in tour]
                if tour[-1] != tour[0]:
                    tour.append(tour[0])
                calculated = sum(float(matrix[a, b]) for a, b in zip(tour, tour[1:]))
                if (
                    len(tour) != n + 1
                    or sorted(tour[:-1]) != list(range(n))
                    or not np.isclose(float(length), calculated, rtol=1e-10, atol=1e-10)
                ):
                    raise ValueError(
                        "Returned tour or length failed independent validation"
                    )
                rows.append(
                    {
                        "graph_id": graph_id,
                        "nodes": n,
                        "method": label,
                        "seed": method_seed,
                        "tour": tour,
                        "length": calculated,
                    }
                )
    summary = []
    for n in nodes:
        ids = [x["graph_id"] for x in inputs if x["nodes"] == n]
        for label in methods:
            values = [
                x["length"] for x in rows if x["nodes"] == n and x["method"] == label
            ]
            if len(values) != len(ids) or len(ids) != graphs:
                raise ValueError("Incomplete paired summary membership")
            summary.append(
                {
                    "nodes": n,
                    "method": label,
                    "n_graphs": len(ids),
                    "graph_ids": ids,
                    "mean_length": float(np.mean(values)),
                    "sample_std": float(np.std(values, ddof=1))
                    if len(values) > 1
                    else None,
                }
            )
    results = {"schema_version": "2.0", "protocol_id": PROTOCOL, "methods": list(METHODS), "parameters": parameters, "graphs": inputs, "observations": rows, "summary": summary}
    validate_results(results, {"schema_version": "2.0", "protocol_id": PROTOCOL, "methods": list(METHODS), "parameters": parameters, "results_sha256": hashlib.sha256(encoded(results)).hexdigest(), "historical_denominator_resolved": False})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nodes", nargs="+", type=int, default=[12, 24])
    parser.add_argument("--graphs", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20261019)
    parser.add_argument("--ants", type=int, default=3)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    destination = Path(os.path.abspath(args.output_dir))
    if (
        destination.is_relative_to(root)
        or destination.exists()
        or not destination.parent.is_dir()
        or any(p.is_symlink() for p in (destination, *destination.parents))
    ):
        parser.error("Use a new external output directory with real existing ancestors")
    sources = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in ("utils.py", "reproduce_comparison.py", "PAPER_REVISION.md", "evidence_validation.py")
    }
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, stdin=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=10).strip()
        clean = not subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True, stdin=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=10).strip()
    except (OSError, subprocess.SubprocessError):
        parser.error("Producer Git identity unavailable")
    if not clean:
        parser.error("Commit the producer source before recording a commit-bound run; use run_comparison for bounded development checks")
    try:
        results = run_comparison(
            args.nodes, args.graphs, args.seed, args.ants, args.iterations
        )
    except ValueError as exc:
        parser.error(str(exc))
    if any(
        hashlib.sha256((root / n).read_bytes()).hexdigest() != h
        for n, h in sources.items()
    ):
        raise ValueError("Sources changed during comparison")
    receipt = {
        "schema_version": "2.0",
        "protocol_id": PROTOCOL,
        "methods": list(METHODS),
        "kind": "new seeded demonstration, not historical Table 1 reconstruction",
        "source_commit": head,
        "source_worktree_clean": clean,
        "source_sha256": sources,
        "runtime": {
            "python": platform.python_version(),
            "packages": {
                p: importlib.metadata.version(p)
                for p in ("numpy", "scipy", "pandas", "matplotlib")
            },
        },
        "parameters": {k: v for k, v in vars(args).items() if k != "output_dir"},
        "results_sha256": hashlib.sha256(encoded(results)).hexdigest(),
        "historical_denominator_resolved": False,
        "interpretation": "Small paired execution and denominator proof only; no historical replication, superiority, significance or generalization claim.",
    }
    verify_sources(receipt, root)
    with tempfile.TemporaryDirectory(
        prefix=".comparison-", dir=destination.parent
    ) as temp:
        folder = Path(temp)
        (folder / "results.json").write_bytes(encoded(results))
        (folder / "receipt.json").write_bytes(encoded(receipt))
        if destination.exists():
            raise ValueError("Output appeared during computation")
        folder.rename(destination)
    print(
        json.dumps(
            {
                "graphs": len(results["graphs"]),
                "observations": len(results["observations"]),
                "results_sha256": receipt["results_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
