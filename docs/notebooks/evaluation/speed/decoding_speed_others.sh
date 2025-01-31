#!/bin/bash

papermill decoding_speed_mwpm.ipynb decoding_speed_mwpm_2.ipynb --autosave-cell-every 3 || sleep 3
papermill decoding_speed_mwpm.ipynb decoding_speed_huf.ipynb --autosave-cell-every 3 -p decoder "huf" -p json_filename "speed-rsc-huf.json" || sleep 3
papermill decoding_speed_mwpm.ipynb decoding_speed_mwpf.ipynb --autosave-cell-every 3 -p decoder "mwpf" -p json_filename "speed-rsc-mwpf.json" || sleep 3
papermill decoding_speed_mwpm.ipynb decoding_speed_bposd_it5.ipynb --autosave-cell-every 3 -p decoder "bposd(max_iter=5)" -p json_filename "speed-rsc-bposd-it5.json" || sleep 3
papermill decoding_speed_mwpm.ipynb decoding_speed_bplsd_it5.ipynb --autosave-cell-every 3 -p decoder "bplsd(max_iter=5)" -p json_filename "speed-rsc-bplsd-it5.json" || sleep 3
papermill decoding_speed_mwpm.ipynb decoding_speed_bpuf_it5.ipynb --autosave-cell-every 3 -p decoder "bpuf(max_iter=5)" -p json_filename "speed-rsc-bpuf-it5.json" || sleep 3
papermill decoding_speed_mwpm.ipynb decoding_speed_bposd.ipynb --autosave-cell-every 3 -p decoder "bposd" -p json_filename "speed-rsc-bposd.json" || sleep 3
papermill decoding_speed_mwpm.ipynb decoding_speed_bplsd.ipynb --autosave-cell-every 3 -p decoder "bplsd" -p json_filename "speed-rsc-bplsd.json" || sleep 3
papermill decoding_speed_mwpm.ipynb decoding_speed_bpuf.ipynb --autosave-cell-every 3 -p decoder "bpuf" -p json_filename "speed-rsc-bpuf.json" || sleep 3
