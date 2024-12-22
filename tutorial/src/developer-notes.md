# Initial setup

I use PyScaffold to set up the Python project

```sh
pip install --upgrade tox sphinx sphinx-rtd-theme pytest pytest-cov pyscaffold[all] pre-commit
# only run once when setting up the project
putup qec_lego_bench

pip install -U pip setuptools -e .
pre-commit install
```
