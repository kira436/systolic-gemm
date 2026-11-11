# Design decisions

Write one short entry per decision. Interviewers read this file first. Use this template:

## <Decision title>
- **Options considered:** A, B, C
- **Chosen:** B
- **Why (with numbers):** e.g. "A needs 2x scratchpad bandwidth; B costs 12% utilization on small M"
- **What I'd change with more time:**

## Decisions to document (suggested)
1. Weight-stationary vs output-stationary
2. Registered vs combinational partial-sum chain (timing vs latency)
3. Accumulator width and overflow policy (wrap vs saturate)
4. Scratchpad banking and double-buffering scheme
5. DMA descriptor format and outstanding-transaction limit
6. Tile sizes and why

## Predicted vs measured
| Shape (M,K,N) | Model cycles | RTL cycles | Delta | Explanation |
|---|---|---|---|---|
| | | | | |
