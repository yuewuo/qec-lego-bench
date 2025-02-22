# Decoder Tests

Here we want to keep track of how the decoders perform across different version.
A couple representative examples are listed below

```sh
python3 -m qec_lego_bench generate-samples 'rsc(d=5,p=0.001)' ./dist/rsc_d5_p001 --mwpf-benchmark-suite --decoder 'mwpf(pass_circuit=1)' --shots 100000
python3 -m qec_lego_bench generate-samples 'rsc(d=3,p=0.001)' ./dist/rsc_d3_p001 --mwpf-benchmark-suite --decoder 'mwpf(pass_circuit=1)' --shots 100000
python3 -m qec_lego_bench generate-samples 'rep(d=3,p=0.001)' ./dist/rep_d3_p001 --mwpf-benchmark-suite --decoder 'mwpf(pass_circuit=1)' --shots 1000000
python3 -m qec_lego_bench generate-samples 'bb(n=72,k=12,d=6)' --noise 'depolarize(p=0.01)' ./dist/bb_d6_p01 --mwpf-benchmark-suite --decoder 'mwpf(pass_circuit=1)' --shots 100000
```
