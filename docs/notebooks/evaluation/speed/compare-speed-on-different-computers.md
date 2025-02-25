# Compare speed on different computers

Here we're interested in comparing speed on M4 Pro vs i7 14700KF on a realistic BB code with circuit-level noise.

To generate the samples:

```sh
python3 -m qec_lego_bench generate-samples 'cbb(n=90,k=8,d=10,p=0.0002)' ./dist/cbb-90-8-10-0002 --shots 20000 --seed 123
```

To run the evaluation:

```sh
python3 -m qec_lego_bench decoding-speed --samples-prefix ./dist/cbb-90-8-10-0002
```

### i7-14700KF

```sh
decoding time: 2.385e-04s, elapsed: 4.770e+00s, shots: 20000
decoding time: 2.392e-04s, elapsed: 4.784e+00s, shots: 20000
decoding time: 2.393e-04s, elapsed: 4.787e+00s, shots: 20000
```

### M1 Max

```sh
decoding time: 1.947e-04s, elapsed: 3.893e+00s, shots: 20000
decoding time: 1.945e-04s, elapsed: 3.890e+00s, shots: 20000
decoding time: 2.006e-04s, elapsed: 4.013e+00s, shots: 20000
```
