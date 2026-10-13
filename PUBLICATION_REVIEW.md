# Publication sample provenance review

Reviewed source: `haailabs/ActiveACO` main `42ed8be` (2026-10-13).
Associated publication: *Enhancing Population-based Search with Active Inference*,
[arXiv:2408.09548](https://arxiv.org/abs/2408.09548).

The archived paper's Section 4.1 describes 100 graphs for each of 50, 100, 250,
and 500 nodes. Table 1 describes 50 graphs per node size and additionally includes
25 nodes. Those are different experiment specifications; neither description
alone establishes the denominator of the published table.

## What this repository establishes

- `main.py` at the reviewed main runs 1,000 graphs at 200 nodes.
- Historical `main.py` at `4a1086ee8e` selects 25 nodes and 50 graphs; at
  `c2bf8f51be` it selects 50 nodes and 100 graphs. The entrypoint changed
  between experiments rather than retaining one paper-wide configuration.
- Figure directories encode several node/sample combinations, including
  `Figures_50_50`, `Figures_100_300`, and `Figures_25_1000`. These names and
  summary statistics are useful context, not proof that any directory is the
  exact source of Table 1.
- The reviewed tracked tree lacks a paper-table receipt binding the exact
  graph identifiers or hashes, random states, method configuration, raw
  per-graph results, and table-generation command to one revision.

## Required reconciliation

Recover the original per-graph inputs/results and run configuration for each
Table 1 column. Record node size, actual graph count, random state, algorithm
parameters, code/environment revision, and input/output hashes in a run manifest.
Rebuild the aggregate table from those rows and correct either the prose or the
table caption according to that evidence. If the original run cannot be
identified, retain the denominator as unresolved; a newly seeded run is a new
experiment, not verification of the old table.

This review does not change experimental values, claim a new benchmark, or
replace the archived arXiv document. It is maintained in the authorized fork;
upstream `haailabs/ActiveACO` remains separately controlled.
