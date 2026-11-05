# Dated saved-evidence audit (2026-11-05)

This audits the already retained October demonstration without rerunning an
optimizer. The original matrices, tours, summary, receipt and README remain
byte-identical. The [descriptive table](table.md) and [membership manifest](membership.json)
report six graphs, eighteen observations and six cells, each with three graphs.
They do not establish the historical paper denominator or any significance,
superiority, timing or generalization result.

The original producer commit is
`0fbd73409db9940200427827b5e8eb235db02ed1`. Producer file hashes were verified
against its exact local Git blobs. The producer runtime in the manifest is the
old receipt's record, not an independently reexecuted runtime. The current
validator's own file hash and Python 3.11.17 identity are recorded separately.
This verifies byte binding and accounting, not scientific validity.

The bounded software suite passed 72 tests on this review date, including the
original seven and corruption/closure/source-provenance checks. It used NumPy
1.26.4, SciPy 1.16.2, pandas 2.3.2, matplotlib 3.10.6 and pytest 8.4.2; no
historical environment was replaced. The saved-data audit itself uses only
Python's standard library and bounded read-only Git commands.

## Artifact hashes

- Original results: `74423dd07c8367947554467f2f2c67910e7e9879ff1cad7e6426f3250d67349c`
- Original receipt: `8827e606c35d409dbaea374829596a7e4cfcb965d41c7ea1fa86db1468fd7895`
- Current membership manifest: `6dcc86b7d388dff2eedb97243d56deadcf4928f971bb79efc502ec93050147e9`
- Current table: `6842184ca94ee10938869e435c2ed3f41c25a0bbde89d97af2eb0c825305fbef`

Run the command in [the main README](../../README.md) with a new external
output directory. The graph identifiers are scoped by the result SHA-256;
another seeded run does not inherit this audit by reusing a short graph name.
