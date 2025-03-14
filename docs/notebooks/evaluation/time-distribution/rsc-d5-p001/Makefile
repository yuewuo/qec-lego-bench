
TARGET_PRECISION := 0.06
JOBS := 8
CPU := "unknown"

EXAMPLE_DECODERS = --decoder 'mwpf(c=0),mwpf(c=50),mwpf(c=200),huf,bposd(max_iter=5;ms_scaling_factor=0.4;osd_order=0;osd_method=cs),bposd(max_iter=5;ms_scaling_factor=0.4;osd_order=10;osd_method=cs)'
examples:
	python3 -m qec_lego_bench notebook-time-distribution rsc-d5-p001-$(CPU).ipynb 'rsc(d=5,p=0.001)' $(EXAMPLE_DECODERS) --target-precision $(TARGET_PRECISION) --local-maximum-jobs $(JOBS) $(EXTRA)

rsc-p0005:
	python3 -m qec_lego_bench notebook-time-distribution rsc-d5-p0005-$(CPU).ipynb 'rsc(d=5,p=0.0005)' $(EXAMPLE_DECODERS) --target-precision $(TARGET_PRECISION) --local-maximum-jobs $(JOBS) $(EXTRA)
