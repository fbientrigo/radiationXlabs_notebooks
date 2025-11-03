"""Convenience exports for the notebooks.

This package exposes the most frequently used helpers at the top-level so that
the notebooks can simply ``import lib`` and access the functionality without
having to remember the internal layout.
"""

from .reading import *
from .detection import *
from .wavelet import *
from .graphing import *  # graphic library, useful plots
from .cpld_io import *
from .cpld_decode import *
from .cpld_events import *
from .cpld_viz import *