# Notebook parameters

## 2025.3.12

on M4 pro Mac Mini: `make rsc CPU=m4pro JOBS=8`, generating `rsc-m4pro.ipynb`
on i7-14700KF with Ubuntu 24.04.2: `make rsc CPU=i7k JOBS=8`, generating `rsc-i7k.ipynb`
on HPC cluster: `srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 make rsc EXTRA="--slurm-maximum-jobs 100"`, generating `rsc-unknown.ipynb`
