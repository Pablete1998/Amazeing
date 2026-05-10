"""
Reusable maze generator module (mazegen).

Implements MazeGenerator using the Recursive Backtracker (DFS) algorithm,
which guarantees perfect mazes: exactly one path between any two cells.

Basic usage:
    from maze_generator import MazeGenerator

    gen = MazeGenerator(width=20, height=15, seed=42)
    gen.generate()
    maze = gen.get_maze()          # 2D list of Cell
    cell = gen.get_cell(0, 0)      # Cell at column=0, row=0
    print(cell.to_hex())           # hex digit of its walls

Custom parameters:
    gen = MazeGenerator(
        width=30,
        height=20,
        seed=1234,                 # seed for reproducibility
        entry=(0, 0),
        exit=(29, 19),
    )
    gen.generate(perfect=False)    # imperfect maze (extra passages)

Accessing the solution:
    from maze_solver import solve_maze
    path = solve_maze(gen, (0, 0), (29, 19))
    # path = ['S', 'E', 'E', 'N', ...]
"""

import random
from dataclasses import dataclass, field
from enum import IntFlag
from typing import Optional


# ---------------------------------------------------------------------------
# Direction constants
# ---------------------------------------------------------------------------

class Wall(IntFlag):
    """
    Bit flags for the four walls of a cell.

    The integer value of a flag combination is the hex digit
    written to the output file:
        bit 0 (value 1) -> NORTH
        bit 1 (value 2) -> EAST
        bit 2 (value 4) -> SOUTH
        bit 3 (value 8) -> WEST
    """

    NORTH = 1
    EAST = 2
    SOUTH = 4
    WEST = 8


# Opposite wall for synchronising adjacent cells
OPPOSITE: dict[Wall, Wall] = {
    Wall.NORTH: Wall.SOUTH,
    Wall.SOUTH: Wall.NORTH,
    Wall.EAST:  Wall.WEST,
    Wall.WEST:  Wall.EAST,
}

# (dx, dy) displacement for each direction
# Y increases downward (row index)
DIRECTION_DELTA: dict[Wall, tuple[int, int]] = {
    Wall.NORTH: (0, -1),
    Wall.SOUTH: (0,  1),
    Wall.EAST:  (1,  0),
    Wall.WEST:  (-1, 0),
}

# Output-file letter for each direction
DIRECTION_LETTER: dict[Wall, str] = {
    Wall.NORTH: "N",
    Wall.EAST:  "E",
    Wall.SOUTH: "S",
    Wall.WEST:  "W",
}

# All walls closed (initial state of every cell)
ALL_WALLS: int = Wall.NORTH | Wall.EAST | Wall.SOUTH | Wall.WEST


# ---------------------------------------------------------------------------
# Cell
# ---------------------------------------------------------------------------

@dataclass
class Cell:
    """
    A single cell in the maze grid.

    Attributes:
        x: Column index (0 = left).
        y: Row index (0 = top).
        walls: Integer encoding active wall bits (Wall flags).
        visited: True once the DFS has processed this cell.
        is_blocked: True if the cell is part of the '42' pattern.
                    Blocked cells keep all walls closed and are
                    ignored by the DFS.
    """

    x: int
    y: int
    walls: int = ALL_WALLS
    visited: bool = False
    is_blocked: bool = False

    def has_wall(self, direction: Wall) -> bool:
        """Return True if the wall in *direction* is closed."""
        return bool(self.walls & direction)

    def remove_wall(self, direction: Wall) -> None:
        """Open the wall in *direction*."""
        self.walls &= ~direction

    def add_wall(self, direction: Wall) -> None:
        """Close the wall in *direction*."""
        self.walls |= direction

    def to_hex(self) -> str:
        """Return the wall value as a single uppercase hex character."""
        return format(self.walls, "X")


# ---------------------------------------------------------------------------
# '42' decorative pattern
# ---------------------------------------------------------------------------

# 1 = blocked cell, 0 = free cell  (7 rows x 11 columns)
_PATTERN_42: list[list[int]] = [
    [1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 0],
    [1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0],
    [1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 0],
    [0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 1, 1, 1, 1, 1, 0],
]
_PAT_H: int = len(_PATTERN_42)       # 7
_PAT_W: int = len(_PATTERN_42[0])    # 11

# Minimum maze size for the pattern to fit with a 2-cell margin
_MIN_W_FOR_PATTERN: int = _PAT_W + 4
_MIN_H_FOR_PATTERN: int = _PAT_H + 4


# ---------------------------------------------------------------------------
# MazeGenerator
# ---------------------------------------------------------------------------

@dataclass
class MazeGenerator:
    """
    Maze generator using the Recursive Backtracker (iterative DFS).

    The DFS visits every free cell exactly once.  On backtracking it
    never reconnects already-visited branches, so the result is always
    a spanning tree of the cell graph — a perfect maze.

    Attributes:
        width: Number of columns.
        height: Number of rows.
        seed: RNG seed for reproducibility (None = random every time).
        entry: (x, y) coordinates of the maze entrance.
        exit: (x, y) coordinates of the maze exit.

    Example:
        >>> gen = MazeGenerator(10, 10, seed=42)
        >>> gen.generate()
        >>> print(gen.get_cell(0, 0).to_hex())
    """

    width: int
    height: int
    seed: Optional[int] = None
    entry: tuple[int, int] = (0, 0)
    exit: tuple[int, int] = (0, 0)
    _grid: list[list[Cell]] = field(default_factory=list, repr=False)
    _rng: random.Random = field(
        default_factory=random.Random, repr=False
    )
    _generated: bool = field(default=False, repr=False)
    _pattern_placed: bool = field(default=False, repr=False)

    def __post_init__(self) -> None:
        """Initialise the private RNG and the grid."""
        # Private Random instance: does not contaminate the global state
        self._rng = random.Random(self.seed)
        self._init_grid()

    def _init_grid(self) -> None:
        """Create the grid with every wall closed."""
        self._grid = [
            [Cell(x=c, y=r) for c in range(self.width)]
            for r in range(self.height)
        ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_cell(self, x: int, y: int) -> Cell:
        """
        Return the cell at position (x, y).

        Args:
            x: Column (0 <= x < width).
            y: Row (0 <= y < height).

        Returns:
            The Cell object at that position.

        Raises:
            IndexError: If the coordinates are out of range.
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise IndexError(
                f"Coordinates ({x},{y}) out of range "
                f"({self.width}x{self.height})"
            )
        return self._grid[y][x]

    def get_maze(self) -> list[list[Cell]]:
        """
        Return the full grid of the maze.

        Returns:
            List of rows; each row is a list of Cell objects.
            Access as grid[row][col] or use get_cell(x, y).
        """
        return self._grid

    def is_generated(self) -> bool:
        """Return True if generate() has been called at least once."""
        return self._generated

    def reset(self, new_seed: Optional[int] = None) -> None:
        """
        Reset the generator to produce a new maze.

        Optionally pass a new seed.  Without one the RNG continues
        from where it left off, producing a different maze each time.

        Args:
            new_seed: New seed, or None to continue the current RNG.
        """
        if new_seed is not None:
            self._rng = random.Random(new_seed)
        self._generated = False
        self._pattern_placed = False
        self._init_grid()

    def generate(self, perfect: bool = True) -> None:
        """
        Generate the maze using iterative Recursive Backtracker (DFS).

        Steps:
          1. Place the '42' pattern (blocked cells).
          2. Pick a random free starting cell.
          3. DFS: from the current cell, pick a random unvisited
             neighbour, remove the wall between them, advance.
             If no unvisited neighbours remain, backtrack (pop stack).
          4. If perfect=False, remove ~5% of internal walls extra.

        Args:
            perfect: True  -> perfect maze (one unique path between
                              entry and exit).
                     False -> add extra passages (multiple routes).
        """
        if self._generated:
            self._init_grid()
            self._pattern_placed = False

        # 1. Decorative '42' pattern
        self._place_pattern_42()

        # 2. Random free starting cell
        sx, sy = self._random_free_cell()
        start = self._grid[sy][sx]
        start.visited = True

        # 3. Iterative DFS
        stack: list[Cell] = [start]
        while stack:
            current = stack[-1]
            neighbours = self._free_unvisited_neighbours(current)
            if neighbours:
                direction, nxt = self._rng.choice(neighbours)
                self._open_wall(current, nxt, direction)
                nxt.visited = True
                stack.append(nxt)
            else:
                stack.pop()

        # 4. Extra passages for imperfect mazes
        if not perfect:
            self._add_extra_paths()

        self._generated = True

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _random_free_cell(self) -> tuple[int, int]:
        """Return (x, y) of a random non-blocked cell."""
        while True:
            x = self._rng.randint(0, self.width - 1)
            y = self._rng.randint(0, self.height - 1)
            if not self._grid[y][x].is_blocked:
                return x, y

    def _free_unvisited_neighbours(
        self, cell: Cell
    ) -> list[tuple[Wall, Cell]]:
        """
        Return unvisited, non-blocked neighbours of a cell.

        Args:
            cell: The current cell.

        Returns:
            List of (direction, neighbour_cell) tuples.
        """
        result: list[tuple[Wall, Cell]] = []
        for direction, (dx, dy) in DIRECTION_DELTA.items():
            nx, ny = cell.x + dx, cell.y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                nb = self._grid[ny][nx]
                if not nb.visited and not nb.is_blocked:
                    result.append((direction, nb))
        return result

    def _open_wall(
        self, cell1: Cell, cell2: Cell, direction: Wall
    ) -> None:
        """
        Remove the wall between two adjacent cells.

        Args:
            cell1: Source cell.
            cell2: Destination cell (neighbour in *direction*).
            direction: Direction from cell1 to cell2.
        """
        cell1.remove_wall(direction)
        cell2.remove_wall(OPPOSITE[direction])

    def _add_extra_paths(self, density: float = 0.05) -> None:
        """
        Open additional internal walls to break perfection.

        Args:
            density: Fraction of cells to process (0.0-1.0).
        """
        count = int(self.width * self.height * density)
        directions = list(DIRECTION_DELTA.keys())
        for _ in range(count):
            x = self._rng.randint(0, self.width - 1)
            y = self._rng.randint(0, self.height - 1)
            cell = self._grid[y][x]
            if cell.is_blocked:
                continue
            d = self._rng.choice(directions)
            dx, dy = DIRECTION_DELTA[d]
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                nb = self._grid[ny][nx]
                if not nb.is_blocked:
                    self._open_wall(cell, nb, d)

    def _place_pattern_42(self) -> None:
        """
        Place the '42' pattern centred in the maze.

        Pattern cells are marked as blocked (is_blocked=True),
        marked as visited so the DFS ignores them, and keep all
        walls closed — forming the visible number '42'.

        If the maze is too small the pattern is skipped and a
        warning is printed (explicitly allowed by the subject).
        """
        if (
            self.width < _MIN_W_FOR_PATTERN
            or self.height < _MIN_H_FOR_PATTERN
        ):
            print(
                "Warning: maze too small for the '42' pattern "
                f"(minimum {_MIN_W_FOR_PATTERN}x{_MIN_H_FOR_PATTERN})."
            )
            return

        ox = (self.width - _PAT_W) // 2
        oy = (self.height - _PAT_H) // 2

        for py, row in enumerate(_PATTERN_42):
            for px, val in enumerate(row):
                if val == 1:
                    cell = self._grid[oy + py][ox + px]
                    cell.is_blocked = True
                    cell.visited = True
                    cell.walls = ALL_WALLS

        self._pattern_placed = True
