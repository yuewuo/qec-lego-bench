# Notebook parameters

## 2025.3.12

on M4 pro Mac Mini: `make rsc CPU=m4pro JOBS=8`, generating `rsc-m4pro.ipynb`
on i7-14700KF with Ubuntu 24.04.2: `make rsc CPU=i7k JOBS=8`, generating `rsc-i7k.ipynb`
on HPC cluster:

```sh
# rsc-unknown.ipynb
srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 make rsc EXTRA="--slurm-maximum-jobs 200"

# rep-unknown.ipynb
srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 make rep EXTRA="--slurm-maximum-jobs 200"
```


## 2025.3.14

After fixing the order of handling the clusters, we could possibly use fewer number of cluster size limit to achieve better accuracy.
Let's test that behavior here, using d=5 and p=0.001, p=0.0005, p=0.0003


```sh
# rsc-unknown.ipynb

nohup srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 make rsc CPU=unknown2-p001 RSC_p=0.001 EXTRA="--slurm-maximum-jobs 200" > unknown2-p001.jobout &
nohup srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 make rsc CPU=unknown2-p0005 RSC_p=0.0005 EXTRA="--slurm-maximum-jobs 200" > unknown2-p0005.jobout &
nohup srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 make rsc CPU=unknown2-p0003 RSC_p=0.0003 EXTRA="--slurm-maximum-jobs 200" > unknown2-p0003.jobout &
```
