# Active ACO

This repository explores nearest-neighbor TSP, basic ant-colony optimization,
and a legacy AI-labelled elitist ACO heuristic. The scalar belief in the labelled
routine cancels when node-choice weights are normalized; its extra elitist
reinforcement is a confound. The label does not establish a distinct active-
inference mechanism or a measured advantage.

## Bounded seeded comparison

Use an isolated environment with NumPy, SciPy, pandas, matplotlib and pytest.
Do not replace a historical environment to match a new execution. The retained
October producer receipt records its own exact versions.

From a clean committed source checkout, choose a new external output directory.
Both commands reserve the directory exclusively and publish the result files before
the completion record (`receipt.json` for comparison and `membership.json` for
audit). If publication is interrupted, inspect the incomplete directory and use
a fresh destination for the next run:

```sh
python reproduce_comparison.py --nodes 12 24 --graphs 3 --seed 20261019 \
  --ants 3 --iterations 5 --output-dir /new/external/comparison
```

This is a small paired execution demonstration, not a reconstruction of the
paper's historical Table 1 or a significance, superiority or timing study.
Raw matrices, seeds, tours, independent scores and exact graph memberships are
retained. New results declare the protocol, method set and parameters. A
commit-bound producer receipt requires a clean source checkout.

When imported, `run_comparison(nodes, graphs, seed, ants, iterations)` restores
the caller's Python and NumPy global random-generator states after success or
failure. This is a serial-use guarantee: the comparison still uses those global
generators while active, so concurrent RNG consumers require separate processes.
Method seeds, returned result fields and the retained historical evidence are
unchanged.

## Audit existing saved evidence without rerunning algorithms

```sh
python evidence_validation.py \
  --results evidence/2026-10-19-comparison/results.json \
  --receipt evidence/2026-10-19-comparison/receipt.json \
  --output-dir /new/external/evidence-audit
```

Omit `--output-dir` for validation only. No network or optimizer execution is
needed. The validator checks matrix structure and hashes, complete paired
membership, method seeds, tours, scores, means and sample standard deviations.
It verifies producer file hashes at the receipt's exact Git commit and refuses
missing objects or mismatches. It does not require those historical hashes to
match today's source. The exporter is identified separately in `membership.json`.
Graph IDs are qualified by the results hash to avoid cross-run ambiguity.

The reviewed [saved-run audit](evidence/2026-11-05-audit/table.md) reports three
graphs per node-size/method cell, six distinct graphs and eighteen observations.
The original [October evidence](evidence/2026-10-19-comparison/README.md) is
preserved. See [PAPER_REVISION.md](PAPER_REVISION.md) for unresolved paper claims.

## Legacy outputs and verification

`main.py`, `visualization.py` and `Figures_*` retain the historical unseeded
plotting workflow. Its expensive default sweep now requires explicit
`--legacy-unseeded` opt-in. Its archived captions and unpaired statistical
procedures are not the seeded protocol and do not resolve the paper denominator.
Do not run that sweep as a smoke test.

```sh
python -m pytest -q test_reproducible_comparison.py test_evidence_validation.py
```

The bounded tests establish software/evidence-accounting behavior only. Any
larger study needs a declared design, retained failures and observations, an
appropriate paired analysis and separately reviewed scientific interpretation.
The arXiv record and original upstream remain separate publication authorities.
