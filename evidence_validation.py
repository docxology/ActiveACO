"""Audit retained paired TSP observations without rerunning any optimizer.

The October 2026 unversioned result schema remains supported explicitly.
Historical producer hashes are checked at their recorded Git commit, never
against today's working files. This does not recover historical Table 1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import statistics
import struct
import subprocess
import tempfile

METHODS = ("nearest_neighbor", "basic_aco", "ai_labelled_elitist_aco")
PROTOCOL = "seeded-paired-tsp-v2"
SOURCE_NAMES = {"utils.py", "reproduce_comparison.py", "PAPER_REVISION.md"}
MAX_JSON_BYTES = 16 * 1024 * 1024


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def _number(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def _digest(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def validate_parameters(parameters):
    _require(isinstance(parameters, dict) and set(parameters) == {"nodes", "graphs", "seed", "ants", "iterations"}, "Invalid protocol parameters")
    nodes = parameters["nodes"]
    _require(isinstance(nodes, list) and nodes and all(_integer(n, 3, 200) for n in nodes) and len(set(nodes)) == len(nodes), "Invalid node sizes")
    for name, upper in (("graphs", 100), ("seed", 2**31 - 1), ("ants", 100), ("iterations", 1000)):
        _require(_integer(parameters[name], 0 if name == "seed" else 1, upper), "Invalid integer parameter: " + name)
    _require(parameters["graphs"] * sum(n * n for n in nodes) <= 100000 and parameters["graphs"] * sum(nodes) * parameters["ants"] * parameters["iterations"] <= 2000000, "Comparison exceeds bounded graph/iteration limits")
    return parameters


def validate_matrix(matrix, nodes, expected_hash=None):
    _require(isinstance(matrix, list) and len(matrix) == nodes and all(isinstance(row, list) and len(row) == nodes for row in matrix), "Invalid matrix shape")
    _require(all(_number(value) for row in matrix for value in row), "Nonfinite or nonnumeric matrix weight")
    for i in range(nodes):
        _require(matrix[i][i] == 0, "Matrix diagonal must be zero")
        for j in range(i):
            _require(matrix[i][j] > 0 and matrix[j][i] > 0 and matrix[i][j] == matrix[j][i], "Matrix must have positive symmetric off-diagonal weights")
    raw = b"".join(struct.pack("<d", value) for row in matrix for value in row)
    digest = hashlib.sha256(raw).hexdigest()
    if expected_hash is not None:
        _require(_digest(expected_hash) and digest == expected_hash, "Matrix float64 little-endian hash mismatch")
    return digest


def _close(actual, expected, label):
    _require(_number(actual) and math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-10), label + " does not match retained observations")


def validate_results(results, receipt, *, results_sha256=None):
    _require(isinstance(results, dict) and isinstance(receipt, dict), "Results and receipt must be objects")
    schema = receipt.get("schema_version")
    _require(schema in ("1.0", "2.0"), "Unsupported receipt schema")
    parameters = validate_parameters(receipt.get("parameters"))
    _require(receipt.get("historical_denominator_resolved") is False, "Historical denominator must remain unresolved")
    if schema == "2.0":
        _require(results.get("schema_version") == "2.0" and results.get("protocol_id") == receipt.get("protocol_id") == PROTOCOL, "Protocol identity mismatch")
        _require(results.get("methods") == receipt.get("methods") == list(METHODS), "Declared method identity mismatch")
        _require(validate_parameters(results.get("parameters")) == parameters, "Result/receipt parameter mismatch")
        results_schema = "2.0"
    else:
        _require(set(results) == {"graphs", "observations", "summary"}, "Unsupported legacy result fields")
        results_schema = "legacy-unversioned"
    digest = results_sha256 if results_sha256 is not None else hashlib.sha256(encoded(results)).hexdigest()
    _require(_digest(receipt.get("results_sha256")) and digest == receipt["results_sha256"], "results SHA-256 hash mismatch")
    nodes, count = parameters["nodes"], parameters["graphs"]
    expected = {f"n{n}-g{i:04d}": (n, (parameters["seed"] + n * 100003 + i * 101) % 2**32) for n in nodes for i in range(count)}
    graphs = results.get("graphs")
    _require(isinstance(graphs, list) and len(graphs) == len(expected), "Graph membership count mismatch")
    indexed = {}
    for graph in graphs:
        _require(isinstance(graph, dict), "Invalid graph record")
        identity = graph.get("graph_id")
        _require(isinstance(identity, str) and identity in expected and identity not in indexed, "Duplicate or unlisted graph identity")
        n, seed = expected[identity]
        _require(type(graph.get("nodes")) is int and graph["nodes"] == n and type(graph.get("seed")) is int and graph["seed"] == seed, "Graph nodes/seed mismatch")
        _require(_digest(graph.get("matrix_f64le_sha256")), "Saved matrix requires a canonical digest")
        validate_matrix(graph.get("matrix"), n, graph["matrix_f64le_sha256"])
        indexed[identity] = graph
    observations = results.get("observations")
    _require(isinstance(observations, list) and len(observations) == len(expected) * len(METHODS), "Observation membership count mismatch")
    observed = {}
    for observation in observations:
        _require(isinstance(observation, dict), "Invalid observation")
        identity, method = observation.get("graph_id"), observation.get("method")
        _require(isinstance(identity, str) and identity in indexed and method in METHODS, "Unknown observation graph or method")
        key = (identity, method)
        _require(key not in observed, "Duplicate graph/method observation")
        n, seed = expected[identity]
        _require(type(observation.get("nodes")) is int and observation["nodes"] == n, "Observation node mismatch")
        _require(type(observation.get("seed")) is int and observation["seed"] == (seed + METHODS.index(method) * 1000003) % 2**32, "Observation method seed mismatch")
        tour = observation.get("tour")
        _require(isinstance(tour, list) and len(tour) == n + 1 and all(type(v) is int for v in tour) and tour[0] == tour[-1] and sorted(tour[:-1]) == list(range(n)), "Invalid closed Hamiltonian tour")
        matrix = indexed[identity]["matrix"]
        length = sum(matrix[a][b] for a, b in zip(tour, tour[1:]))
        _close(observation.get("length"), length, "Tour length")
        observed[key] = length
    _require(set(observed) == {(identity, method) for identity in expected for method in METHODS}, "Methods do not share complete paired graph membership")
    summary = results.get("summary")
    _require(isinstance(summary, list) and len(summary) == len(nodes) * len(METHODS), "Summary membership count mismatch")
    summaries = {}
    for row in summary:
        _require(isinstance(row, dict), "Invalid summary")
        n, method = row.get("nodes"), row.get("method")
        _require(type(n) is int and n in nodes and method in METHODS and (n, method) not in summaries, "Duplicate or unknown summary")
        identities = [identity for identity, (size, _) in expected.items() if size == n]
        _require(type(row.get("n_graphs")) is int and row["n_graphs"] == len(identities) and row.get("graph_ids") == identities, "Summary denominator/membership mismatch")
        values = [observed[(identity, method)] for identity in identities]
        mean = statistics.mean(values)
        deviation = statistics.stdev(values) if len(values) > 1 else None
        _close(row.get("mean_length"), mean, "Summary mean")
        if deviation is None:
            _require(row.get("sample_std") is None, "Singleton has no sample standard deviation")
        else:
            _close(row.get("sample_std"), deviation, "Summary standard deviation")
        summaries[n, method] = {"nodes": n, "method": method, "n_graphs": len(identities), "graph_ids": identities, "qualified_graph_ids": [digest + ":" + identity for identity in identities], "mean_length": mean, "sample_std": deviation}
    return {"schema_version": "1.0", "kind": "saved paired evidence audit; not historical Table 1 reconstruction", "results_schema": results_schema, "protocol_id": PROTOCOL if schema == "2.0" else "legacy October 2026 seed/method protocol", "results_sha256": digest, "source_commit": receipt.get("source_commit"), "source_binding_verified": False, "producer_runtime": receipt.get("runtime"), "parameters": parameters, "methods": list(METHODS), "n_graphs": len(indexed), "n_observations": len(observed), "historical_denominator_resolved": False, "summaries": [summaries[n, method] for n in nodes for method in METHODS]}


def load_json(path):
    return _decode_json(_read_json_bytes(path))


def _read_json_bytes(path):
    path = Path(path)
    _require(path.is_file() and path.stat().st_size <= MAX_JSON_BYTES, "Missing or oversized JSON evidence")
    with path.open("rb") as stream:
        raw = stream.read(MAX_JSON_BYTES + 1)
    _require(len(raw) <= MAX_JSON_BYTES, "Oversized JSON evidence")
    return raw


def _decode_json(raw):
    _require(len(raw) <= MAX_JSON_BYTES, "Oversized JSON evidence")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            _require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result

    def nonfinite(_):
        raise ValueError("Nonfinite JSON number")

    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique, parse_constant=nonfinite)


def verify_sources(receipt, source_root):
    commit = receipt.get("source_commit")
    _require(isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit) is not None, "Invalid historical source commit")
    _require(receipt.get("source_worktree_clean") is True, "A dirty producer is not bound by the recorded commit")
    names = SOURCE_NAMES | ({"evidence_validation.py"} if receipt.get("schema_version") == "2.0" else set())
    sources = receipt.get("source_sha256")
    _require(isinstance(sources, dict) and set(sources) == names and all(_digest(value) for value in sources.values()), "Invalid producer source paths or hashes")
    runtime = receipt.get("runtime")
    _require(isinstance(runtime, dict) and isinstance(runtime.get("python"), str) and runtime["python"], "Missing producer Python identity")
    packages = runtime.get("packages")
    _require(isinstance(packages, dict) and all(isinstance(packages.get(name), str) and packages[name] for name in ("numpy", "scipy", "pandas", "matplotlib")), "Missing producer dependency versions")
    for name, digest in sources.items():
        try:
            raw = subprocess.check_output(["git", "-C", str(Path(source_root).resolve()), "show", commit + ":" + name], stdin=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=10)
        except (OSError, subprocess.SubprocessError) as exc:
            raise ValueError("Recorded producer source object unavailable: " + name) from exc
        _require(len(raw) <= 1024 * 1024 and hashlib.sha256(raw).hexdigest() == digest, "Recorded producer source hash mismatch: " + name)
    return True


def audit_saved(results_path, receipt_path, source_root):
    # Parse and hash one snapshot of each artifact; a second read could bind
    # a different concurrent version from the one whose observations we audit.
    results_raw, receipt_raw = _read_json_bytes(results_path), _read_json_bytes(receipt_path)
    results, receipt = _decode_json(results_raw), _decode_json(receipt_raw)
    digest = hashlib.sha256(results_raw).hexdigest()
    manifest = validate_results(results, receipt, results_sha256=digest)
    verify_sources(receipt, source_root)
    manifest.update(source_binding_verified=True, receipt_sha256=hashlib.sha256(receipt_raw).hexdigest(), producer_source_sha256=receipt["source_sha256"], validator={"name": "evidence_validation.py", "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "python": platform.python_version()})
    return manifest


def render_table(manifest):
    lines = ["# Retained paired-run denominator audit", "", "This is not a reconstruction of historical Table 1. These are descriptive", "summaries of the identified new October 2026 demonstration, with no superiority,", "significance, timing or generalization claim.", "", "Results SHA-256: `" + manifest["results_sha256"] + "`.", "Producer source commit: `" + str(manifest.get("source_commit")) + "`.", "Producer source bindings verified: " + str(manifest["source_binding_verified"]).lower() + ".", "", "| Nodes | Method | Observed graphs | Mean tour length | Sample SD | Graph IDs |", "| --- | --- | ---: | ---: | ---: | --- |"]
    for row in manifest["summaries"]:
        sd = "not estimated (one graph)" if row["sample_std"] is None else f'{row["sample_std"]:.6f}'
        lines.append(f'| {row["nodes"]} | {row["method"]} | {row["n_graphs"]} | {row["mean_length"]:.6f} | {sd} | ' + ", ".join(row["graph_ids"]) + " |")
    lines += ["", "Every listed method has exactly one independently checked Hamiltonian tour", "on each listed graph. Pairing refers to graph membership; methods retain", "their distinct recorded RNG seeds. Graph IDs are local to this results hash;", "the companion manifest qualifies them as `<results SHA-256>:<graph ID>`.", "", "The AI-labelled heuristic includes elitist reinforcement. Its common scalar", "belief cancels during normalized node choice; these observations do not", "establish a distinct active-inference mechanism.", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        manifest = audit_saved(args.results, args.receipt, args.source_root)
        if args.output_dir is not None:
            destination = Path(os.path.abspath(args.output_dir))
            root = Path(__file__).resolve().parent
            _require(not destination.exists() and destination.parent.is_dir() and not destination.is_relative_to(root) and not any(path.is_symlink() for path in (destination, *destination.parents)), "Use a new external output directory with real existing ancestors")
            with tempfile.TemporaryDirectory(prefix=".evidence-audit-", dir=destination.parent) as temporary:
                folder = Path(temporary)
                (folder / "membership.json").write_bytes(encoded(manifest))
                (folder / "table.md").write_text(render_table(manifest), encoding="utf-8")
                _require(not destination.exists(), "Output appeared during validation")
                folder.rename(destination)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps({"graphs": manifest["n_graphs"], "observations": manifest["n_observations"], "results_sha256": manifest["results_sha256"], "source_binding_verified": manifest["source_binding_verified"]}))


if __name__ == "__main__":
    main()
