

C_VEC := 0 1 2 3 5 7 10 15 20 30 50 70 100 200 500 1000
MWPF_DECODERS := $(foreach c,$(C_VEC),--decoder 'mwpf(c=$(c))')
MWPFI_DECODERS := $(foreach c,$(C_VEC),--decoder 'mwpfi(c=$(c))')  # incremental LP
MWPFD_DECODERS := $(foreach c,$(C_VEC),--decoder 'mwpfd(c=$(c))')  # default (without gxhash)
SPLIT := --decoder none
DECODERS := $(MWPF_DECODERS) $(SPLIT) $(MWPFI_DECODERS) $(SPLIT) $(MWPFD_DECODERS)

TARGET_PRECISION := 0.06
JOBS := 10
CPU := "unknown"

decoders:
	@echo "$(DECODERS)"

# example: make color CPU=m1max JOBS=8

color:
	python3 -m qec_lego_bench notebook-compare-decoder color-$(CPU).ipynb 'color(d=5,p=0.0001)' $(DECODERS) --target-precision $(TARGET_PRECISION) --local-maximum-jobs $(JOBS)

rsc:
	python3 -m qec_lego_bench notebook-compare-decoder rsc-$(CPU).ipynb 'rsc(d=5,p=0.001)' $(DECODERS) --target-precision $(TARGET_PRECISION) --local-maximum-jobs $(JOBS)
