# Corrected methods and results boundary

This is a proposed source correction for *Enhancing Population-based Search with
Active Inference*. It is maintained in the authorized `docxology/ActiveACO` fork;
the arXiv record and upstream repository remain separate publication authorities.

## Replacement text for the sample-size description and Table 1 note

The historical Section 4.1 and Table 1 specify different node/sample designs.
The available repository does not bind the published table to per-graph inputs,
observations and a table-generation receipt. The number of graphs supporting
each historical table column is therefore not established. Neither prose value
should be selected as the corrected denominator without that evidence. Pending
recovery of the original run, the table cannot support a sample-size-dependent
inferential conclusion. Historical values are retained as an archival record,
not as reproduced results of this source correction.

## Reproducible replacement protocol

`reproduce_comparison.py` creates a *new* seeded paired demonstration. Each
node-size/method summary lists the exact graph IDs and observed graph count.
Every graph is saved as a full matrix with a canonical float64 little-endian
hash. Every method runs on the same identified graph and retains its RNG seed,
tour and independently recomputed length. Source/dependency bindings accompany
the raw results. A single graph has no estimated sample standard deviation.

```bash
python reproduce_comparison.py --nodes 12 24 --graphs 3 --seed 20261019 \
  --ants 3 --iterations 5 --output-dir /new/external/comparison
```

These small execution defaults are not a new population-scale performance
claim. Scaling the protocol requires a declared design and its own retained
results. No historical table or significance result is reconstructed by a new
seeded execution.

## Algorithm attribution

The current active-inference-labelled routine includes elitist pheromone
reinforcement. Its node-choice expression multiplies every candidate weight by
the same scalar belief before normalizing; that scalar cancels from the
categorical distribution. A difference from basic ACO cannot therefore be
attributed to that scalar as a distinct action-dependent inference mechanism.
The runner uses an explicit heuristic label and makes no causal attribution to
active inference. A principled algorithm revision would be a separately
specified and evaluated method, not a silent change to the historical code.


## Distance and graph-generation correction

Independent tour checks exposed a scoring defect: the labelled heuristic returns
an explicitly closed tour, while its scorer added another closing self-edge.
The generator could assign nonzero diagonal weights after masking/scaling, so
that extra term changed the reported distance. A shared scorer now normalizes
open/closed tour representations and counts every Hamiltonian edge once. The
generator now also preserves its declared symmetry through masking and resets
the diagonal after scaling. Regression tests cover nonzero input diagonals,
closed/open equivalence, symmetric generation, and valid tours. These source
corrections apply to new executions and do not retroactively correct archived
tables without their raw inputs.


## Saved-evidence validation follow-up (2026-11-05)

The retained October demonstration can now be audited without a new optimization
run. `evidence_validation.py` checks the full matrices, canonical float64 hashes,
expected graph IDs and seeds, one observation per graph/method, closed tours and
independently recomputed lengths. Every summary denominator, membership list,
mean and sample standard deviation is checked against those observations. Missing,
duplicate or foreign members fail rather than silently changing the denominator.
Singleton cells retain no estimated sample standard deviation.

The [dated descriptive table](evidence/2026-11-05-audit/table.md) and companion
membership manifest concern only six retained graphs (three each at 12 and 24
nodes), eighteen method observations and six summary cells. All three methods
share graph membership, while their recorded method seeds differ. Run-qualified
graph identities include the result SHA-256. No historical sample size, p-value,
timing, superiority or population-scale performance is inferred.

The October result and receipt bytes remain unchanged. Their producer commit is
`0fbd73409db9940200427827b5e8eb235db02ed1`; the current validator reads and hashes
the named files at that exact Git object. Today's validator/exporter identity is
recorded separately. A missing historical object or source-hash mismatch blocks
export. This verifies identified bytes and accounting, not an independently
reexecuted historical runtime or scientific validity.

Future runs declare version 2 of the seed/method protocol explicitly and retain
their own committed source and dependency identities. Source recording refuses a
dirty producer checkout; every Git reader has closed stdin and a bounded timeout.
The old unused `free_energy` helper was never called and has been removed; no
free-energy minimization claim follows from the legacy heuristic. Its numerical
choice and reinforcement rules are retained. `main.py` is marked as a historical
unseeded sweep and requires an explicit opt-in, preventing accidental large runs
through the primary usage instructions.
