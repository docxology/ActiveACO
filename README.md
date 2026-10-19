# Active ACO

## Overview
This repository includes implementations of various optimization algorithms for the Traveling Salesman Problem (TSP):
- Nearest Neighbor TSP
- Ant Colony Optimization (ACO)
- Improved ACO with Active Inference

Active inference is based on the concept that perception is an active process, involving the minimization of free energy and continuous updating of beliefs based on environmental interactions. This repository explores ACO variants on randomly generated graphs. Comparative or inferential claims require identified runs; the active-inference label does not establish a distinct inferred mechanism. See [the corrected paper protocol](PAPER_REVISION.md).

## Files
- `main.py`: Script to run experiments, compare methods, and generate plots.
- `utils.py`: Contains the implementations of the optimization algorithms and utility functions.
- `visualization.py`: Functions for generating plots to visualize the results.

## Usage
Run `main.py` to generate graphs and compare the algorithms. Results are presented both numerically in tables and visually in plots.

## Requirements
Ensure all dependencies are installed:
- numpy
- pandas
- matplotlib
- seaborn
- scipy

For a bounded new seeded comparison with raw inputs, tours, exact denominators
and source/runtime receipts, use `reproduce_comparison.py` as documented in
[PAPER_REVISION.md](PAPER_REVISION.md). Historical figure summaries remain archived.
