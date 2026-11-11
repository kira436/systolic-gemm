import numpy as np
from model.golden import gemm_int8, wrap, PEState, pe_step
from model.perf_model import ws_utilization, gemm_intensity


def test_gemm_matches_numpy_int32():
    rng = np.random.default_rng(0)
    A = rng.integers(-128, 128, (7, 9), dtype=np.int8)
    B = rng.integers(-128, 128, (9, 5), dtype=np.int8)
    assert (gemm_int8(A, B) == A.astype(np.int32) @ B.astype(np.int32)).all()


def test_wrap():
    assert wrap(128, 8) == -128 and wrap(-129, 8) == 127 and wrap(2**31, 32) == -(2**31)


def test_pe_contract():
    s = pe_step(PEState(), 1, 3, 0, 0)
    s = pe_step(s, 0, 0, 5, 10)
    assert s.psum_out == 25 and s.a_out == 5


def test_utilization_grows_with_M():
    assert ws_utilization(512, 128, 128, 128, 128) > ws_utilization(16, 128, 128, 128, 128)


def test_decode_like_gemm_is_low_intensity():
    assert gemm_intensity(1, 4096, 4096) < 5   # batch-1: bandwidth-bound regime
