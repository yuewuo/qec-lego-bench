#!/bin/bash

srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 -p day     papermill ./logical-error-rate-bb72.ipynb logical-error-rate-bb72-2.ipynb --autosave-cell-every 10 


srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 -p day     papermill ./logical-error-rate-rsc-consistency-mwpm.ipynb ./logical-error-rate-rsc-consistency-mwpm-2.ipynb
srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 -p day     papermill ./logical-error-rate-rsc-consistency-mwpf.ipynb ./logical-error-rate-rsc-consistency-mwpf-2.ipynb
srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 -p day     papermill ./logical-error-rate-rsc-consistency-huf.ipynb ./logical-error-rate-rsc-consistency-huf-2.ipynb
