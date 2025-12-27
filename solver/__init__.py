"""
T-Tetracube 6×6×6 Cube Solver

This package implements an exact cover solver using Algorithm X (Dancing Links)
to enumerate all distinct tilings of a 6×6×6 cube using 54 identical T-tetracubes,
up to rotational symmetry.

Mathematical Foundation:
- Board: 6×6×6 = 216 cells
- Piece: T-tetracube (4 unit cubes in T-shape)
- Pieces needed: 216/4 = 54
- Symmetry group: Rotation group of cube (24 elements)
"""

__version__ = "1.0.0"
