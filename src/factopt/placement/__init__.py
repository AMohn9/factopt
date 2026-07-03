"""Spatial placement of block entities.

Only the dense direct-insertion row placer remains here: it is the one placer
wired into the general place-and-route loop (wrapped as a ``MacroCell`` by the
``dense`` strategy in :mod:`factopt.macros.library`). Recipe ordering for
placement lives in :mod:`factopt.placement.ordering`.
"""

from factopt.placement.dense import (
    DenseBoundaryPort,
    DensePlacement,
    place_dense_row,
)

__all__ = [
    "place_dense_row",
    "DensePlacement",
    "DenseBoundaryPort",
]
