from importlib.metadata import PackageNotFoundError, version  # pragma: no cover

from . import cli
from . import codes
from . import decoders
from . import noises

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError
