"""goes16tiler"""

__version_info__ = (1,0,0)
__version__ = '.'.join([str(n) for n in __version_info__])

__author__ = "Stuart Illson"

from .goes16tiler import GOES16Tiler

__all__ = [
    "GOES16Tiler"
]