"""First-order performance model. Every formula here is an ASSUMPTION to be calibrated against RTL cycle counts."""
import math


def roofline(peak_ops_per_s: float, bw_bytes_per_s: float, intensity_ops_per_byte: float) -> float:
    """Attainable ops/s = min(peak compute, bandwidth * arithmetic intensity)."""
    return min(peak_ops_per_s, bw_bytes_per_s * intensity_ops_per_byte)


def gemm_intensity(M: int, K: int, N: int, bytes_in: int = 1, bytes_out: int = 4) -> float:
    """Ops per byte for C[MxN] = A[MxK] @ B[KxN], counting each operand and the result once (ideal reuse)."""
    ops = 2 * M * K * N
    traffic = (M * K + K * N) * bytes_in + M * N * bytes_out
    return ops / traffic


def ws_cycles(M: int, K: int, N: int, rows: int, cols: int) -> int:
    """Weight-stationary estimate. K maps to array rows, N to array columns, M streams through.
    Per tile: `rows` cycles to load weights + M cycles of streaming + (rows + cols - 2) fill/drain skew.
    TODO: replace with measured RTL cycles and explain the deltas in docs/design_decisions.md."""
    tiles = math.ceil(K / rows) * math.ceil(N / cols)
    return tiles * (rows + M + rows + cols - 2)


def ws_utilization(M: int, K: int, N: int, rows: int, cols: int) -> float:
    """Useful MACs / (PEs * cycles)."""
    return (M * K * N) / (rows * cols * ws_cycles(M, K, N, rows, cols))
