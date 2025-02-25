# Compare speed on different computers

Here we're interested in comparing speed on M4 Pro vs i7 14700KF on a realistic BB code with circuit-level noise.

To generate the samples:

```sh
python3 -m qec_lego_bench generate-samples 'cbb(n=90,k=8,d=10,p=0.0002)' ./dist/cbb-90-8-10-0002 --shots 20000 --seed 123
```

To run the evaluation:

```sh
python3 -m qec_lego_bench benchmark-samples ./dist/cbb-90-8-10-0002
```

### i7-14700KF

```sh
# --decoder mwpf
decoding time: 2.385e-04s, elapsed: 4.770e+00s, shots: 20000
decoding time: 2.392e-04s, elapsed: 4.784e+00s, shots: 20000
decoding time: 2.393e-04s, elapsed: 4.787e+00s, shots: 20000
# --decoder 'bposd(max_iter=1000,ms_scaling_factor=1,osd_order=10,osd_method=osd_cs)'
decoding time: 2.300e-04s, elapsed: 4.599e+00s, shots: 20000
decoding time: 2.307e-04s, elapsed: 4.615e+00s, shots: 20000
decoding time: 2.344e-04s, elapsed: 4.687e+00s, shots: 20000
```

### M1 Max

```sh
# --decoder mwpf
decoding time: 1.947e-04s, elapsed: 3.893e+00s, shots: 20000
decoding time: 1.945e-04s, elapsed: 3.890e+00s, shots: 20000
decoding time: 2.006e-04s, elapsed: 4.013e+00s, shots: 20000
# --decoder 'bposd(max_iter=1000,ms_scaling_factor=1,osd_order=10,osd_method=osd_cs)'
decoding time: 3.397e-04s, elapsed: 6.794e+00s, shots: 20000
decoding time: 3.397e-04s, elapsed: 6.794e+00s, shots: 20000
decoding time: 3.428e-04s, elapsed: 6.856e+00s, shots: 20000
```

### M4 Pro (Binned/Base Version, 512GB SSD, 24GB RAM)
```sh
# --decoder mwpf
decoding time: 1.321e-04s, elapsed: 2.641e+00s, shots: 20000
decoding time: 1.319e-04s, elapsed: 2.639e+00s, shots: 20000
decoding time: 1.346e-04s, elapsed: 2.693e+00s, shots: 20000
```
