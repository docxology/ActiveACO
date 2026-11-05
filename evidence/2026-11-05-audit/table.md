# Retained paired-run denominator audit

This is not a reconstruction of historical Table 1. These are descriptive
summaries of the identified new October 2026 demonstration, with no superiority,
significance, timing or generalization claim.

Results SHA-256: `74423dd07c8367947554467f2f2c67910e7e9879ff1cad7e6426f3250d67349c`.
Producer source commit: `0fbd73409db9940200427827b5e8eb235db02ed1`.
Producer source bindings verified: true.

| Nodes | Method | Observed graphs | Mean tour length | Sample SD | Graph IDs |
| --- | --- | ---: | ---: | ---: | --- |
| 12 | nearest_neighbor | 3 | 21.147753 | 13.467915 | n12-g0000, n12-g0001, n12-g0002 |
| 12 | basic_aco | 3 | 12.224308 | 16.864445 | n12-g0000, n12-g0001, n12-g0002 |
| 12 | ai_labelled_elitist_aco | 3 | 12.598046 | 17.909119 | n12-g0000, n12-g0001, n12-g0002 |
| 24 | nearest_neighbor | 3 | 63.361899 | 43.826900 | n24-g0000, n24-g0001, n24-g0002 |
| 24 | basic_aco | 3 | 65.867879 | 52.252219 | n24-g0000, n24-g0001, n24-g0002 |
| 24 | ai_labelled_elitist_aco | 3 | 69.498958 | 55.227968 | n24-g0000, n24-g0001, n24-g0002 |

Every listed method has exactly one independently checked Hamiltonian tour
on each listed graph. Pairing refers to graph membership; methods retain
their distinct recorded RNG seeds. Graph IDs are local to this results hash;
the companion manifest qualifies them as `<results SHA-256>:<graph ID>`.

The AI-labelled heuristic includes elitist reinforcement. Its common scalar
belief cancels during normalized node choice; these observations do not
establish a distinct active-inference mechanism.
