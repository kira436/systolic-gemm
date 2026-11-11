# systolic-gemm

Weight-stationary INT8 GEMM accelerator in SystemVerilog, with a bit-accurate Python golden model, a first-order
performance model, and a cocotb/Verilator regression.

> **Status:** WIP. Milestone 1 of 5: processing element (see Roadmap).

## Overview
One-paragraph summary: what it computes (`C[MxN] = A[MxK] x B[KxN]`, INT8 in, INT32 out), the array size, and the
headline result (e.g. "X% utilization at M=512; model within Y% of RTL"). Fill this in last.

## Architecture
![block diagram](docs/arch.png)

- PE array (R x C), weight-stationary dataflow
- Double-buffered scratchpad (banks, ports)
- DMA engine (2D strided)
- Control FSM

## Interface contract (PE)
| Signal | Dir | Width | Description |
|---|---|---|---|
| clk, rst_n | in | 1 | clock, synchronous active-low reset |
| load_w | in | 1 | latch `w_in` as the stationary weight |
| w_in, a_in | in | 8 signed | weight / activation |
| psum_in | in | 32 signed | partial sum from the north neighbor |
| a_out | out | 8 signed | activation passed east (registered) |
| psum_out | out | 32 signed | partial sum passed south (registered) |

Update rule is documented in `model/golden.py:pe_step` and is the single source of truth.

## Results
| Config | Peak (MAC/cycle) | Utilization (M=512) | Fmax / area (open flow) |
|---|---|---|---|
| 4x4 | 16 | TBD | TBD |

## Quick start
```bash
pip install -r requirements.txt
make test-model      # golden + perf model tests (no simulator needed)
make sim             # cocotb + Verilator regression
```
Requires Verilator 5.x.

## Verification
- Directed + constrained-random tests, scoreboard against `model/golden.py`
- SVA assertions: TBD
- Coverage: TBD

## Performance model
`model/perf_model.py`: roofline, arithmetic intensity, weight-stationary cycle/utilization estimate.
Calibration against RTL is tracked in `docs/design_decisions.md`.

## Design decisions
See `docs/design_decisions.md`.

## Limitations
List them honestly (supported shapes, no sparsity, wrap-on-overflow, single clock domain, ...).

## Roadmap
- [ ] 1. PE + cocotb tests
- [ ] 2. 4x4 array + golden-model check
- [ ] 3. Scratchpad + DMA
- [ ] 4. Perf model calibrated to RTL, utilization plots
- [ ] 5. SVA assertions, optional formal (SymbiYosys), Yosys area/timing

## References
- Jouppi et al., In-Datacenter Performance Analysis of a TPU (ISCA 2017)
- Sze et al., Efficient Processing of Deep Neural Networks

## License
MIT
