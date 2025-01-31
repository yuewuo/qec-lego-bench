#!/bin/bash

srun --time=1-00:00:00 --mem=10G --cpus-per-task=2 -p day     papermill ./logical-error-rate-bb72.ipynb logical-error-rate-bb72-2.ipynb --autosave-cell-every 10 

