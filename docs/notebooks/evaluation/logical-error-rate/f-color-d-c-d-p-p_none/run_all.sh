#!/bin/bash

# prefix start
RID=zz-2
# prefix end

tmux new-session -d -s mwpf_f-color-d-c-d-p-p_none "srun --time=23:55:00 --mem=10G --cpus-per-task=2 papermill mwpf.ipynb ${RID}.mwpf.ipynb"
tmux new-session -d -s huf_f-color-d-c-d-p-p_none "srun --time=23:55:00 --mem=10G --cpus-per-task=2 papermill huf.ipynb ${RID}.huf.ipynb"
tmux new-session -d -s f-mwpf-c-50-c-d_f-color-d-c-d-p-p_none "srun --time=23:55:00 --mem=10G --cpus-per-task=2 papermill f-mwpf-c-50-c-d.ipynb ${RID}.f-mwpf-c-50-c-d.ipynb"
tmux new-session -d -s bposd_f-color-d-c-d-p-p_none "srun --time=23:55:00 --mem=10G --cpus-per-task=2 papermill bposd.ipynb ${RID}.bposd.ipynb"
tmux new-session -d -s bposd-max-iter-5_f-color-d-c-d-p-p_none "srun --time=23:55:00 --mem=10G --cpus-per-task=2 papermill bposd-max-iter-5.ipynb ${RID}.bposd-max-iter-5.ipynb"
tmux new-session -d -s bposd-max-iter-5-osd-order-10-osd-method-osd-e_f-color-d-c-d-p-p_none "srun --time=23:55:00 --mem=10G --cpus-per-task=2 papermill bposd-max-iter-5-osd-order-10-osd-method-osd-e.ipynb ${RID}.bposd-max-iter-5-osd-order-10-osd-method-osd-e.ipynb"
tmux new-session -d -s bpuf_f-color-d-c-d-p-p_none "srun --time=23:55:00 --mem=10G --cpus-per-task=2 papermill bpuf.ipynb ${RID}.bpuf.ipynb"
tmux new-session -d -s bpuf-max-iter-5_f-color-d-c-d-p-p_none "srun --time=23:55:00 --mem=10G --cpus-per-task=2 papermill bpuf-max-iter-5.ipynb ${RID}.bpuf-max-iter-5.ipynb"
