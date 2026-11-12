"""cocotb testbench for rtl/systolic_array.sv, checked against model/golden.py:gemm_int8.

Mapping (weight-stationary): PE[r][c] holds W[r][c]; row r is fed column r of A (A[m, r]);
psums flow down each column, so bottom output c for streamed row m = sum_r A[m, r] * W[r, c],
i.e. C = A @ W, which is exactly gemm_int8(A, W).
"""
import numpy as np
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from model.golden import gemm_int8, wrap

N = 4   # array is N x N; must match the ROWS/COLS parameters of systolic_array


async def start(dut):
    """Start a 10 ns clock, drive every input to a known value, and hold reset for 3 cycles."""
    cocotb.start_soon(Clock(dut.clk, 10, "ns").start())
    dut.rst_n.value = 0
    dut.wr_en.value = 0
    dut.wr_row.value = 0
    dut.wr_col.value = 0
    dut.wr_data.value = 0
    dut.a_in.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


def check(dut, A, W, got):
    """Compare the DUT result with the golden model; on mismatch, log both matrices and fail."""
    exp = gemm_int8(A, W)
    if not np.array_equal(got, exp):
        dut._log.error(f"A=\n{A}\nW=\n{W}\nexpected=\n{exp}\ngot=\n{got}")
        bad = np.argwhere(got != exp)
        assert False, f"{len(bad)} mismatching elements, first at (m, c) = {tuple(bad[0])}"


async def run_gemm(dut, A, W, n=4):
    M = A.shape[0]
    # 1) load weights, one per cycle
    for r in range(n):
        for c in range(n):
            dut.wr_en.value, dut.wr_row.value, dut.wr_col.value = 1, r, c
            dut.wr_data.value = int(W[r, c]) & 0xFF
            await RisingEdge(dut.clk)
    dut.wr_en.value = 0
    # 2) stream activations; row r is delayed by r cycles
    C = np.zeros((M, n), dtype=np.int64)
    for t in range(M + 2*n - 2):
        v = 0
        for r in range(n):
            m = t - r
            val = int(A[m, r]) if 0 <= m < M else 0
            v |= (val & 0xFF) << (8 * r)
        dut.a_in.value = v
        await RisingEdge(dut.clk); await Timer(1, "ns")
        for c in range(n):
            m = t - c - (n - 1)               # hypothesis: verify on the waveform
            if 0 <= m < M:
                C[m, c] = wrap((int(dut.psum_out.value) >> (32*c)) & 0xFFFFFFFF, 32)
    return C

@cocotb.test()
async def identity_weights(dut):
    """W = identity, so C must equal A. Easiest case to debug on the waveform."""
    await start(dut)
    A = np.arange(1, 4 * N + 1, dtype=np.int8).reshape(4, N)   # rows 1..4, 5..8, ...
    W = np.eye(N, dtype=np.int8)
    check(dut, A, W, await run_gemm(dut, A, W, N))


@cocotb.test()
async def directed_small(dut):
    """Hand-checkable values, including negatives."""
    await start(dut)
    A = np.array([[1, 2, 3, 4], [-1, -2, -3, -4]], dtype=np.int8)
    W = np.array([[1, 0, 0, 2], [0, 1, 0, 2], [0, 0, 1, 2], [1, 1, 1, 1]], dtype=np.int8)
    check(dut, A, W, await run_gemm(dut, A, W, N))


@cocotb.test()
async def extremes(dut):
    """Largest-magnitude INT8 values: -128 * -128 products summed over all rows."""
    await start(dut)
    for a_val, w_val in ((-128, -128), (127, -128), (127, 127)):
        A = np.full((3, N), a_val, dtype=np.int8)
        W = np.full((N, N), w_val, dtype=np.int8)
        check(dut, A, W, await run_gemm(dut, A, W, N))


@cocotb.test()
async def random_gemm(dut):
    """Random matrices with different M (number of streamed rows), back to back without reset."""
    await start(dut)
    rng = np.random.default_rng(1234)
    for M in (1, 2, 4, 7, 16, 33):
        A = rng.integers(-128, 128, size=(M, N), dtype=np.int8)
        W = rng.integers(-128, 128, size=(N, N), dtype=np.int8)
        check(dut, A, W, await run_gemm(dut, A, W, N))
