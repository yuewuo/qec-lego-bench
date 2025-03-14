

## 2025.2.28

```sh
tmux new-session -d -s cbb-n72-p001 "srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 python3 -m qec_lego_bench notebook-bp-tuner ./cbb-n72-p001.ipynb 'cbb(n=72,k=12,d=6,p=0.001)' --slurm-maximum-jobs 200 --max-cpu-hours 200"

# tmux new-session -d -s cbb-n72-p002 "srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 python3 -m qec_lego_bench notebook-bp-tuner ./cbb-n72-p002.ipynb 'cbb(n=72,k=12,d=6,p=0.002)' --slurm-maximum-jobs 50 --max-cpu-hours 50"

# tmux new-session -d -s cbb-n72-p002-osd5 "srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 python3 -m qec_lego_bench notebook-bp-tuner ./cbb-n72-p002-osd5.ipynb 'cbb(n=72,k=12,d=6,p=0.002)' --decoder 'bposd(osd_order=5,osd_method=cs)' --slurm-maximum-jobs 50 --max-cpu-hours 50"
```

## 2025.3.13

Try to understand how BP decoder works with MWPF decoders

```sh
tmux new-session -d -s cbb-n72-p002-mwpf-c0 "srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 python3 -m qec_lego_bench notebook-bp-tuner ./cbb-n72-p002-mwpf-c0.ipynb 'cbb(n=72,k=12,d=6,p=0.002)' --slurm-maximum-jobs 100 --max-cpu-hours 200 --decoder 'mwpf(c=0,bp=1)'"

tmux new-session -d -s cbb-n72-p002-mwpf-c50 "srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 python3 -m qec_lego_bench notebook-bp-tuner ./cbb-n72-p002-mwpf-c50.ipynb 'cbb(n=72,k=12,d=6,p=0.002)' --slurm-maximum-jobs 100 --max-cpu-hours 200 --decoder 'mwpf(c=50,bp=1)'"

tmux new-session -d -s cbb-n72-p002-mwpf-c200 "srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 python3 -m qec_lego_bench notebook-bp-tuner ./cbb-n72-p002-mwpf-c200.ipynb 'cbb(n=72,k=12,d=6,p=0.002)' --slurm-maximum-jobs 100 --max-cpu-hours 200 --decoder 'mwpf(c=200,bp=1)'"
```
