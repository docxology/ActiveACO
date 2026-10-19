# New paired execution evidence

These raw matrices, tours and summaries were produced twice with identical
result bytes from the clean source commit recorded in `receipt.json`. The
receipt binds source hashes, dependencies, parameters and result SHA-256.

This bounded demonstration establishes execution and denominator accounting
for the saved run. It does not reproduce historical Table 1, recover its sample
size, or establish significance, superiority or generalization. See
[the source correction](../../PAPER_REVISION.md).

To reproduce, check out the receipt's source commit, install its recorded
runtime dependencies in an isolated environment, then run:

```sh
python reproduce_comparison.py --nodes 12 24 --graphs 3 --seed 20261019 \
  --ants 3 --iterations 5 --output-dir /new/external/comparison
```

Compare the SHA-256 of `results.json` with the recorded digest. Receipt source
identity refers to the execution commit, which predates this evidence-only
commit; it does not describe the working tree after adding these files.
