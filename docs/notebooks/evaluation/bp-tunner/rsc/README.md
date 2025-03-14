

## 2025.2.28

```sh
# tmux new-session -d -s rsc-d5-p01-osd1 "srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 python3 -m qec_lego_bench notebook-bp-tuner ./rsc-d5-p01-osd1.ipynb 'rsc(d=5,p=0.01)' --decoder 'bposd(osd_order=1,osd_method=cs)' --slurm-maximum-jobs 50 --max-cpu-hours 50"
# tmux new-session -d -s rsc-d5-p01-osd5 "srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 python3 -m qec_lego_bench notebook-bp-tuner ./rsc-d5-p01-osd5.ipynb 'rsc(d=5,p=0.01)' --decoder 'bposd(osd_order=5,osd_method=cs)' --slurm-maximum-jobs 50 --max-cpu-hours 50"

# tmux new-session -d -s rsc-d5-p003-osd1 "srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 python3 -m qec_lego_bench notebook-bp-tuner ./rsc-d5-p003-osd1.ipynb 'rsc(d=5,p=0.003)' --decoder 'bposd(osd_order=1,osd_method=cs)' --slurm-maximum-jobs 100 --max-cpu-hours 100"
# tmux new-session -d -s rsc-d5-p003-osd5 "srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 python3 -m qec_lego_bench notebook-bp-tuner ./rsc-d5-p003-osd5.ipynb 'rsc(d=5,p=0.003)' --decoder 'bposd(osd_order=5,osd_method=cs)' --slurm-maximum-jobs 100 --max-cpu-hours 100"

tmux new-session -d -s rsc-d5-p001-osd1 "srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 python3 -m qec_lego_bench notebook-bp-tuner ./rsc-d5-p001-osd1.ipynb 'rsc(d=5,p=0.001)' --decoder 'bposd(osd_order=1,osd_method=cs)' --slurm-maximum-jobs 200 --max-cpu-hours 200"
tmux new-session -d -s rsc-d5-p001-osd5 "srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 python3 -m qec_lego_bench notebook-bp-tuner ./rsc-d5-p001-osd5.ipynb 'rsc(d=5,p=0.001)' --decoder 'bposd(osd_order=5,osd_method=cs)' --slurm-maximum-jobs 200 --max-cpu-hours 200"



# tmux new-session -d -s rsc-d3-p01 "srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 python3 -m qec_lego_bench notebook-bp-tuner ./rsc-d3-p01.ipynb 'rsc(d=3,p=0.01)' --slurm-maximum-jobs 50 --max-cpu-hours 50"

# tmux new-session -d -s rsc-d5-p01 "srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 python3 -m qec_lego_bench notebook-bp-tuner ./rsc-d5-p01.ipynb 'rsc(d=5,p=0.01)' --slurm-maximum-jobs 50 --max-cpu-hours 50"

# tmux new-session -d -s rsc-d3-p001 "srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 python3 -m qec_lego_bench notebook-bp-tuner ./rsc-d3-p001.ipynb 'rsc(d=3,p=0.001)' --slurm-maximum-jobs 50 --max-cpu-hours 50"

# tmux new-session -d -s rsc-d5-p001 "srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 python3 -m qec_lego_bench notebook-bp-tuner ./rsc-d5-p001.ipynb 'rsc(d=5,p=0.001)' --slurm-maximum-jobs 200 --max-cpu-hours 200"

tmux new-session -d -s rsc-d3-p003 "srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 python3 -m qec_lego_bench notebook-bp-tuner ./rsc-d3-p003.ipynb 'rsc(d=3,p=0.003)' --slurm-maximum-jobs 50 --max-cpu-hours 50"

tmux new-session -d -s rsc-d5-p003 "srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 python3 -m qec_lego_bench notebook-bp-tuner ./rsc-d5-p003.ipynb 'rsc(d=5,p=0.003)' --slurm-maximum-jobs 50 --max-cpu-hours 50"
```


## 2025.3.13

Try to understand how BP decoder works with MWPF decoders

```sh
tmux new-session -d -s bp-tuner-c0 "srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 python3 -m qec_lego_bench notebook-bp-tuner ./rsc-d5-p001-mwpf-c0.ipynb 'rsc(d=5,p=0.001)' --slurm-maximum-jobs 100 --max-cpu-hours 200 --decoder 'mwpf(c=0,bp=1)'"

tmux new-session -d -s bp-tuner-c50 "srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 python3 -m qec_lego_bench notebook-bp-tuner ./rsc-d5-p001-mwpf-c50.ipynb 'rsc(d=5,p=0.001)' --slurm-maximum-jobs 100 --max-cpu-hours 200 --decoder 'mwpf(c=50,bp=1)'"

tmux new-session -d -s bp-tuner-c200 "srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 python3 -m qec_lego_bench notebook-bp-tuner ./rsc-d5-p001-mwpf-c200.ipynb 'rsc(d=5,p=0.001)' --slurm-maximum-jobs 100 --max-cpu-hours 200 --decoder 'mwpf(c=200,bp=1)'"
```
