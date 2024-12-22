# Initial setup

I use PyScaffold to set up the Python project

```sh
pip install --upgrade tox sphinx sphinx-rtd-theme pytest pytest-cov pyscaffold[all] pre-commit
# only run once when setting up the project
putup qec_lego_bench

pip install -U pip setuptools -e .
pre-commit install

tox -e docs  # to build your documentation
tox -e build  # to build your package distribution
tox -e publish  # to test your project uploads correctly in test.pypi.org
tox -e publish -- --repository pypi  # to release your package to PyPI
tox -av  # to list all the tasks available
```
