# Usage:  make sim        (cocotb + Verilator, PE testbench)
#         make test-model (pure-Python golden/perf-model tests, no simulator needed)
SIM ?= verilator
TOPLEVEL_LANG ?= verilog
VERILOG_SOURCES = $(PWD)/rtl/pe.sv $(PWD)/rtl/systolic_array.sv
TOPLEVEL = systolic_array
COCOTB_TOPLEVEL = systolic_array
MODULE = tests.test_array
COCOTB_TEST_MODULES = tests.test_array
EXTRA_ARGS += --trace --trace-structs -Wno-fatal
export PYTHONPATH := $(PWD):$(PYTHONPATH)

sim: all

include $(shell cocotb-config --makefiles)/Makefile.sim

test-model:
	python -m pytest -q tests/test_golden.py

clean::
	rm -rf results.xml sim_build __pycache__ */__pycache__ *.vcd *.fst
