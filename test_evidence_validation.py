"""Saved-data checks do not rerun optimizers or recover historical Table 1."""

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parent
SAVED = ROOT / "evidence" / "2026-10-19-comparison"


def api():
    import evidence_validation

    return evidence_validation


@pytest.fixture
def saved():
    return (
        json.loads((SAVED / "results.json").read_text()),
        json.loads((SAVED / "receipt.json").read_text()),
    )


def checked(results, receipt):
    receipt = copy.deepcopy(receipt)
    receipt["results_sha256"] = hashlib.sha256(api().encoded(results)).hexdigest()
    return api().validate_results(results, receipt)


def test_retained_run_has_exact_current_denominators_and_qualified_membership(saved):
    results, receipt = saved
    manifest = checked(results, receipt)
    assert manifest["n_graphs"] == 6
    assert manifest["n_observations"] == 18
    assert manifest["historical_denominator_resolved"] is False
    assert manifest["results_schema"] == "legacy-unversioned"
    assert len(manifest["summaries"]) == 6
    for row in manifest["summaries"]:
        assert row["n_graphs"] == 3
        assert row["graph_ids"] == [f'n{row["nodes"]}-g{i:04d}' for i in range(3)]
        assert row["qualified_graph_ids"] == [
            receipt["results_sha256"] + ":" + name for name in row["graph_ids"]
        ]
    table = api().render_table(manifest)
    assert "not a reconstruction of historical Table 1" in table
    assert "| 12 | nearest_neighbor | 3 |" in table
    assert "| 24 | ai_labelled_elitist_aco | 3 |" in table
    assert receipt["results_sha256"] in table


@pytest.mark.parametrize("mutation", ["missing_graph", "duplicate_graph", "foreign_graph", "wrong_nodes", "wrong_seed"])
def test_graph_membership_is_closed_and_matches_declared_design(saved, mutation):
    results, receipt = saved
    if mutation == "missing_graph":
        results["graphs"].pop()
    elif mutation == "duplicate_graph":
        results["graphs"].append(copy.deepcopy(results["graphs"][0]))
    elif mutation == "foreign_graph":
        results["graphs"][0]["graph_id"] = "unlisted"
    elif mutation == "wrong_nodes":
        results["graphs"][0]["nodes"] = 24
    else:
        results["graphs"][0]["seed"] += 1
    with pytest.raises(ValueError):
        checked(results, receipt)


@pytest.mark.parametrize("mutation", ["shape", "asymmetry", "diagonal", "nonpositive", "nonfinite", "enormous", "boolean", "null_hash", "hash"])
def test_matrix_structure_and_canonical_bytes_are_independently_checked(saved, mutation):
    results, receipt = saved
    graph = results["graphs"][0]
    if mutation == "shape":
        graph["matrix"][0].pop()
    elif mutation == "asymmetry":
        graph["matrix"][0][1] += 0.25
    elif mutation == "diagonal":
        graph["matrix"][0][0] = 1
    elif mutation == "nonpositive":
        graph["matrix"][0][1] = graph["matrix"][1][0] = 0
    elif mutation == "nonfinite":
        graph["matrix"][0][1] = float("nan")
    elif mutation == "enormous":
        graph["matrix"][0][1] = 10 ** 500
    elif mutation == "boolean":
        graph["matrix"][0][1] = True
    elif mutation == "null_hash":
        graph["matrix_f64le_sha256"] = None
    else:
        graph["matrix_f64le_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        checked(results, receipt)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "foreign", "unknown_method", "nodes", "seed", "tour", "open_tour", "boolean_tour", "length"])
def test_each_method_has_one_valid_scored_tour_on_every_identified_graph(saved, mutation):
    results, receipt = saved
    observation = results["observations"][0]
    if mutation == "missing":
        results["observations"].pop()
    elif mutation == "duplicate":
        results["observations"].append(copy.deepcopy(observation))
    elif mutation == "foreign":
        observation["graph_id"] = "foreign"
    elif mutation == "unknown_method":
        observation["method"] = "unregistered"
    elif mutation == "nodes":
        observation["nodes"] = 24
    elif mutation == "seed":
        observation["seed"] += 1
    elif mutation == "tour":
        observation["tour"][1] = observation["tour"][0]
    elif mutation == "open_tour":
        observation["tour"].pop()
    elif mutation == "boolean_tour":
        observation["tour"][0] = False
    else:
        observation["length"] += 1
    with pytest.raises(ValueError):
        checked(results, receipt)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "count", "membership", "mean", "std", "nodes", "method"])
def test_tables_are_recomputed_from_complete_paired_observations(saved, mutation):
    results, receipt = saved
    row = results["summary"][0]
    if mutation == "missing":
        results["summary"].pop()
    elif mutation == "duplicate":
        results["summary"].append(copy.deepcopy(row))
    elif mutation == "count":
        row["n_graphs"] = 100
    elif mutation == "membership":
        row["graph_ids"] = row["graph_ids"][:-1]
    elif mutation == "mean":
        row["mean_length"] += 1
    elif mutation == "std":
        row["sample_std"] += 1
    elif mutation == "nodes":
        row["nodes"] = 25
    else:
        row["method"] = "unregistered"
    with pytest.raises(ValueError):
        checked(results, receipt)


def test_result_bytes_are_bound_before_validation(saved):
    results, receipt = saved
    receipt["results_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="results.*hash|results.*SHA"):
        api().validate_results(results, receipt)


def test_versioned_future_protocol_cannot_change_method_identity(saved):
    results, receipt = saved
    results.update(schema_version="2.0", protocol_id="seeded-paired-tsp-v2", methods=list(api().METHODS), parameters=receipt["parameters"])
    receipt.update(schema_version="2.0", protocol_id="seeded-paired-tsp-v2", methods=list(api().METHODS))
    assert checked(results, receipt)["results_schema"] == "2.0"
    results["methods"][2] = "active_inference_proven"
    with pytest.raises(ValueError):
        checked(results, receipt)


@pytest.mark.parametrize("parameter,value", [("graphs", 1.0), ("graphs", True), ("seed", True), ("ants", 1.0), ("iterations", True)])
def test_future_result_parameters_have_strict_types_independently_of_receipt(parameter, value):
    from reproduce_comparison import run_comparison
    results = run_comparison([4], 1, 1, 1, 1)
    receipt = {"schema_version": "2.0", "protocol_id": results["protocol_id"], "methods": list(results["methods"]), "parameters": copy.deepcopy(results["parameters"]), "historical_denominator_resolved": False}
    results["parameters"][parameter] = value
    with pytest.raises(ValueError):
        checked(results, receipt)


@pytest.mark.parametrize("key,value", [("graphs", True), ("graphs", 3.0), ("seed", True), ("ants", 3.0), ("iterations", False)])
def test_saved_parameters_have_strict_integer_types(saved, key, value):
    results, receipt = saved
    receipt["parameters"][key] = value
    with pytest.raises(ValueError):
        checked(results, receipt)


def test_retained_receipt_sources_are_verified_at_the_recorded_commit():
    manifest = api().audit_saved(SAVED / "results.json", SAVED / "receipt.json", ROOT)
    assert manifest["source_commit"] == "0fbd73409db9940200427827b5e8eb235db02ed1"
    assert manifest["source_binding_verified"] is True
    assert manifest["receipt_sha256"] == hashlib.sha256((SAVED / "receipt.json").read_bytes()).hexdigest()


@pytest.mark.parametrize("mutation", ["source_hash", "source_path", "commit", "missing_commit", "dirty_source", "historical_claim"])
def test_invalid_receipt_fails_closed_without_writing_a_table(tmp_path, saved, mutation):
    results, receipt = saved
    if mutation == "source_hash":
        receipt["source_sha256"]["utils.py"] = "0" * 64
    elif mutation == "source_path":
        receipt["source_sha256"]["../outside.py"] = "0" * 64
    elif mutation == "commit":
        receipt["source_commit"] = "not-an-object-id"
    elif mutation == "missing_commit":
        receipt["source_commit"] = "0" * 40
    elif mutation == "dirty_source":
        receipt["source_worktree_clean"] = False
    else:
        receipt["historical_denominator_resolved"] = True
    (tmp_path / "results.json").write_bytes(api().encoded(results))
    (tmp_path / "receipt.json").write_bytes(api().encoded(receipt))
    output = tmp_path / "new-table"
    with pytest.raises(SystemExit):
        api().main(["--results", str(tmp_path / "results.json"), "--receipt", str(tmp_path / "receipt.json"), "--source-root", str(ROOT), "--output-dir", str(output)])
    assert not output.exists()


@pytest.mark.parametrize("payload", ['{"graphs": [], "graphs": []}', '{"graphs": NaN}'])
def test_duplicate_or_nonfinite_json_is_refused_before_provenance_use(tmp_path, payload):
    path = tmp_path / "bad.json"
    path.write_text(payload)
    with pytest.raises(ValueError):
        api().load_json(path)


def test_source_git_reads_have_no_stdin_and_a_timeout(monkeypatch, saved):
    _, receipt = saved
    calls = []
    original = subprocess.check_output

    def record(*args, **kwargs):
        calls.append(kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(subprocess, "check_output", record)
    api().verify_sources(receipt, ROOT)
    assert len(calls) == 3
    assert all(call["stdin"] == subprocess.DEVNULL and 0 < call["timeout"] <= 10 for call in calls)


def test_legacy_main_requires_explicit_expensive_workflow_opt_in(tmp_path):
    # Never invoke the historical sweep when testing the missing guard itself.
    assert "--legacy-unseeded" in (ROOT / "main.py").read_text()
    result = subprocess.run([sys.executable, "-B", str(ROOT / "main.py")], cwd=tmp_path, stdin=subprocess.DEVNULL, text=True, capture_output=True, timeout=20)
    assert result.returncode == 2
    assert "--legacy-unseeded" in result.stderr
    assert not list(tmp_path.glob("Figures_*"))
