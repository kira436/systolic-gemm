"""cocotb testbench for rtl/pe.sv, checked cycle-by-cycle against model/golden.py:pe_step."""
import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from model.golden import PEState, pe_step, wrap


def as_signed(sig, bits):
    return wrap(int(sig.value), bits)       # int() gives the unsigned bit pattern; wrap() reinterprets it


async def start(dut):
    cocotb.start_soon(Clock(dut.clk, 10, "ns").start())
    dut.rst_n.value = 0
    dut.load_w.value = 0
    dut.w_in.value = 0
    dut.a_in.value = 0
    dut.psum_in.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1


async def step(dut, st, load_w, w, a, p):
    """Drive inputs, advance one clock, compare DUT outputs with the model's next state."""
    dut.load_w.value, dut.w_in.value = load_w, w & 0xFF
    dut.a_in.value, dut.psum_in.value = a & 0xFF, p & 0xFFFFFFFF
    exp = pe_step(st, load_w, w, a, p)
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert as_signed(dut.a_out, 8) == exp.a_out, f"a_out {as_signed(dut.a_out, 8)} != {exp.a_out}"
    assert as_signed(dut.psum_out, 32) == exp.psum_out, f"psum_out {as_signed(dut.psum_out, 32)} != {exp.psum_out}"
    return exp


@cocotb.test()
async def directed_load_then_mac(dut):
    await start(dut)
    st = PEState()
    st = await step(dut, st, 1, 3, 0, 0)       # load weight = 3
    st = await step(dut, st, 0, 0, 5, 10)      # 10 + 5*3 = 25
    st = await step(dut, st, 0, 0, -7, 100)    # 100 + (-7*3) = 79


@cocotb.test()
async def extremes(dut):
    await start(dut)
    st = PEState()
    for w in (-128, 127):
        st = await step(dut, st, 1, w, 0, 0)
        for a in (-128, 127, 0, -1):
            for p in (0, 2**31 - 1, -(2**31)):   # accumulator overflow wraps; contract says it wraps
                st = await step(dut, st, 0, 0, a, p)


@cocotb.test()
async def random_stream(dut):
    await start(dut)
    random.seed(1234)
    st = PEState()
    for _ in range(5000):
        load = 1 if random.random() < 0.05 else 0
        st = await step(dut, st, load, random.randint(-128, 127), random.randint(-128, 127),
                        random.randint(-2**31, 2**31 - 1))
