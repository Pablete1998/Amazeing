"""
mazegen -- Reusable maze generator.

Exports the main classes and functions for use in other projects.

Quick start:
    from mazegen import MazeGenerator, solve_maze

    gen = MazeGenerator(width=20, height=15, seed=42)
    gen.generate()
    path = solve_maze(gen, (0, 0), (19, 14))
    print("".join(path))   # e.g. 'SSEENE...'
"""

from mazegen.generator import (
    MazeGenerator,
    Cell,
    Wall,
    OPPOSITE,
    DIRECTION_DELTA,
    DIRECTION_LETTER,
)
from mazegen.solver import solve_maze

__all__ = [
    "MazeGenerator",
    "Cell",
    "Wall",
    "OPPOSITE",
    "DIRECTION_DELTA",
    "DIRECTION_LETTER",
    "solve_maze",
]
