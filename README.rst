.. These are examples of badges you might want to add to your README:
   please update the URLs accordingly

    .. image:: https://api.cirrus-ci.com/github/<USER>/qec_lego_bench.svg?branch=main
        :alt: Built Status
        :target: https://cirrus-ci.com/github/<USER>/qec_lego_bench
    .. image:: https://readthedocs.org/projects/qec_lego_bench/badge/?version=latest
        :alt: ReadTheDocs
        :target: https://qec_lego_bench.readthedocs.io/en/stable/
    .. image:: https://img.shields.io/coveralls/github/<USER>/qec_lego_bench/main.svg
        :alt: Coveralls
        :target: https://coveralls.io/r/<USER>/qec_lego_bench
    .. image:: https://img.shields.io/pypi/v/qec_lego_bench.svg
        :alt: PyPI-Server
        :target: https://pypi.org/project/qec_lego_bench/
    .. image:: https://img.shields.io/conda/vn/conda-forge/qec_lego_bench.svg
        :alt: Conda-Forge
        :target: https://anaconda.org/conda-forge/qec_lego_bench
    .. image:: https://pepy.tech/badge/qec_lego_bench/month
        :alt: Monthly Downloads
        :target: https://pepy.tech/project/qec_lego_bench
    .. image:: https://img.shields.io/twitter/url/http/shields.io.svg?style=social&label=Twitter
        :alt: Twitter
        :target: https://twitter.com/qec_lego_bench

.. image:: https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold
    :alt: Project generated with PyScaffold
    :target: https://pyscaffold.org/

|

==============
QEC Lego Bench
==============


    A benchmark suite for quantum error correction decoding system following the LEGO architecture.


    Current Status: very early development and may not be ready for use. Though sometimes it may allow others to quickly rerun the simulation in my paper so it's worth sharing. Especially, the command line tool allows running the simulation with zero lines of programming.


Real-time QEC decoding is needed for large-scale fault-tolerant quantum computation.
Yet there exists no standard way to benchmark the performance of QEC decoders, both in terms of speed and accuracy, across different quantum error models and code sizes.
This project aims to provide a benchmark suite for QEC decoders following the LEGO architecture, which is a modular and extensible architecture for QEC decoders.
Importantly, the benchmark suite mimics the behavior of real quantum computers by streaming the error syndrome data to the decoder in real-time.
In this way, the overall logical error rate of the decoder can be evaluated taking into considering the decoding latency and its induced idle logical errors.

We take into consideration future QEC decoding systems that are distributed across multiple compute units, e.g., FPGAs, CPUs and GPUs,
and our benchmark suite targets this heterogeneous and distributed setting.
It will not be sufficient for software implementations to generate the real-time syndrome data at the large scale, so we design an extensible interface
such that hardware-accelerated simulators can be plugged into the evaluation suite.
Ultimately, the benchmark suite should get rid of the need for software if all the data are exchanged within an FPGA.
In that case, the benchmark suite merely becomes a host that configures the hardware to run both Clifford circuit simulator and the real-time decoding system.



.. _pyscaffold-notes:

Note
====

This project has been set up using PyScaffold 4.6. For details and usage
information on PyScaffold see https://pyscaffold.org/.
