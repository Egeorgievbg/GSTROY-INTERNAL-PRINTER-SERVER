"""Blueprint registry for gstroy server."""

from .core import bp_core
from .printers import bp_printers

__all__ = ["bp_core", "bp_printers"]
