import pytest
from reproduce_comparison import run_comparison, encoded


def test_paired_graph_membership_and_reproducible_results():
    first = run_comparison([4, 5], 2, 123, 2, 2)
    second = run_comparison([4, 5], 2, 123, 2, 2)
    assert encoded(first) == encoded(second)
    assert len(first["graphs"]) == 4
    assert len(first["observations"]) == 12
    for row in first["summary"]:
        assert row["n_graphs"] == len(row["graph_ids"]) == 2
        matching = [
            r
            for r in first["observations"]
            if r["nodes"] == row["nodes"] and r["method"] == row["method"]
        ]
        assert [r["graph_id"] for r in matching] == row["graph_ids"]


def test_single_graph_has_no_sample_standard_deviation():
    assert all(
        r["sample_std"] is None for r in run_comparison([4], 1, 1, 1, 1)["summary"]
    )


@pytest.mark.parametrize(
    "nodes,graphs,ants,iterations",
    [([2], 1, 1, 1), ([10, 10], 1, 1, 1), ([200], 100, 100, 1000)],
)
def test_resource_and_design_bounds(nodes, graphs, ants, iterations):
    with pytest.raises(ValueError):
        run_comparison(nodes, graphs, 1, ants, iterations)


def test_open_and_closed_tours_do_not_count_a_nonzero_diagonal():
    import numpy as np
    from utils import tour_distance, improved_aco_active_inference

    matrix = np.array([[99.0, 1.0, 3.0], [1.0, 88.0, 2.0], [3.0, 2.0, 77.0]])
    assert tour_distance(matrix, [0, 1, 2]) == 6.0
    assert tour_distance(matrix, [0, 1, 2, 0]) == 6.0
    tour, length = improved_aco_active_inference(matrix, num_ants=1, num_iterations=1)
    assert length == tour_distance(matrix, tour) == 6.0


def test_generated_tsp_graphs_remain_symmetric_without_self_loops():
    import numpy as np
    from utils import generate_random_graphs

    np.random.seed(20261019)
    for matrix in generate_random_graphs(5, 6):
        assert np.array_equal(matrix, matrix.T)
        assert np.array_equal(matrix.diagonal(), np.zeros(6))
        assert (matrix[~np.eye(6, dtype=bool)] > 0).all()


@pytest.mark.parametrize("parameter,value", [("graphs", True), ("graphs", 2.0), ("seed", 1.0), ("seed", True), ("ants", False), ("iterations", 1.0)])
def test_runner_refuses_noninteger_design_parameters(parameter, value):
    parameters = dict(nodes=[4], graphs=1, seed=1, ants=1, iterations=1)
    parameters[parameter] = value
    with pytest.raises(ValueError):
        run_comparison(**parameters)


@pytest.mark.parametrize("mutation", ["asymmetry", "diagonal"])
def test_runner_refuses_invalid_generated_graph_structure(monkeypatch, mutation):
    import numpy as np
    import reproduce_comparison

    graph = np.ones((4, 4)) - np.eye(4)
    if mutation == "asymmetry":
        graph[0, 1] = 2
    else:
        graph[0, 0] = 1
    monkeypatch.setattr(reproduce_comparison, "generate_random_graphs", lambda *_: [graph])
    with pytest.raises(ValueError):
        run_comparison([4], 1, 1, 1, 1)


def test_new_results_declare_protocol_and_singleton_summary_is_auditable():
    from evidence_validation import validate_results, METHODS
    import hashlib

    results = run_comparison([4], 1, 1, 1, 1)
    assert results["schema_version"] == "2.0"
    assert results["protocol_id"] == "seeded-paired-tsp-v2"
    assert results["methods"] == list(METHODS)
    receipt = {"schema_version": "2.0", "protocol_id": results["protocol_id"], "methods": results["methods"], "parameters": results["parameters"], "results_sha256": hashlib.sha256(encoded(results)).hexdigest(), "historical_denominator_resolved": False}
    manifest = validate_results(results, receipt)
    assert all(row["sample_std"] is None and row["n_graphs"] == 1 for row in manifest["summaries"])



def _next_caller_random_values():
    import random
    import numpy as np

    return {
        "python": [random.random() for _ in range(4)],
        "numpy": np.random.random(4).tolist(),
    }


@pytest.fixture
def caller_random_streams():
    import random
    import numpy as np

    python_state = random.getstate()
    numpy_state = np.random.get_state(legacy=False)
    try:
        random.seed(45928)
        np.random.seed(4321)
        expected = _next_caller_random_values()
        random.seed(45928)
        np.random.seed(4321)
        yield expected
    finally:
        random.setstate(python_state)
        np.random.set_state(numpy_state)


@pytest.mark.parametrize("stream", ["python", "numpy"])
def test_run_comparison_preserves_caller_rng_on_success(caller_random_streams, stream):
    run_comparison([4], 1, 123, 1, 1)
    assert _next_caller_random_values()[stream] == caller_random_streams[stream]


@pytest.mark.parametrize("stream", ["python", "numpy"])
def test_run_comparison_preserves_caller_rng_on_failure(
    caller_random_streams, stream, monkeypatch
):
    import random

    def unavailable_random_start(*args, **kwargs):
        raise RuntimeError("controlled random source failure")

    # Fail at the random-source boundary in basic ACO, after graph generation
    # and the nearest-neighbor observation have completed.
    monkeypatch.setattr(random, "randint", unavailable_random_start)
    with pytest.raises(RuntimeError, match="controlled random source failure"):
        run_comparison([4], 1, 123, 1, 1)
    assert _next_caller_random_values()[stream] == caller_random_streams[stream]
