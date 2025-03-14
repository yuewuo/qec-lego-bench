

C_VEC := 0 1 2 3 5 7 10 15 20 30 50 70 100 200 500 1000
MWPF_DECODERS := $(foreach c,$(C_VEC),--decoder 'mwpf(c=$(c))')
MWPFI_DECODERS := $(foreach c,$(C_VEC),--decoder 'mwpfi(c=$(c))')  # incremental LP
MWPFD_DECODERS := $(foreach c,$(C_VEC),--decoder 'mwpfd(c=$(c))')  # default (without gxhash)
SPLIT := --decoder none
ALL_MWPF_DECODERS := $(MWPF_DECODERS) $(SPLIT) $(MWPFI_DECODERS) $(SPLIT) $(MWPFD_DECODERS)
OSD_ORDER_VEC := 0 1 2 3 4 5 6 7 8 9 10
EXTRA := 

TARGET_PRECISION := 0.06
JOBS := 8
CPU := "unknown"

decoders:
	@echo "$(ALL_MWPF_DECODERS)"

# example: make color CPU=m1max JOBS=8

COLOR_DECODERS := $(ALL_MWPF_DECODERS)
color:
	python3 -m qec_lego_bench notebook-compare-decoder color-$(CPU).ipynb 'color(d=5,p=0.0001)' $(COLOR_DECODERS) --target-precision $(TARGET_PRECISION) --local-maximum-jobs $(JOBS) $(EXTRA)

RSC_OSD_ORDER_VEC := 0 1 3 10  # because  1 ~ 10 doesn't change much
RSC_OSD_DECODERS := $(foreach order,$(RSC_OSD_ORDER_VEC),--decoder 'bposd(max_iter=5;ms_scaling_factor=0.4;osd_order=$(order);osd_method=cs)')
RSC_BP_MWPF_DECODERS := $(foreach c,$(C_VEC),--decoder 'mwpf(c=$(c);bp=1;max_iter=5;ms_scaling_factor=0.4)')
RSC_DECODERS := $(ALL_MWPF_DECODERS) $(SPLIT) $(RSC_OSD_DECODERS) $(SPLIT) $(RSC_BP_MWPF_DECODERS)
rsc:
	python3 -m qec_lego_bench notebook-compare-decoder rsc-$(CPU).ipynb 'rsc(d=5,p=0.001)' $(RSC_DECODERS) --target-precision $(TARGET_PRECISION) --local-maximum-jobs $(JOBS) $(EXTRA)

REP_OSD_DECODERS := $(foreach order,$(OSD_ORDER_VEC),--decoder 'bposd(max_iter=50;ms_scaling_factor=0.9;osd_order=$(order);osd_method=cs)')
REP_BP_MWPF_DECODERS := $(foreach c,$(C_VEC),--decoder 'mwpf(c=$(c);bp=1;max_iter=50;ms_scaling_factor=0.9)')
REP_DECODERS := $(ALL_MWPF_DECODERS) $(SPLIT) $(REP_OSD_DECODERS) $(SPLIT) $(REP_BP_MWPF_DECODERS)
rep: 
	python3 -m qec_lego_bench notebook-compare-decoder rep-$(CPU).ipynb 'rep(d=13,p=0.01)' $(REP_DECODERS) --target-precision $(TARGET_PRECISION) --local-maximum-jobs $(JOBS) $(EXTRA)
