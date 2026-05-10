"""
Maze solver module.

Functions:
  - solve_maze: BFS shortest path between entry and exit.
  - write_output: Write the hexadecimal output file.
"""

from collections import deque
from typing import Optional

from maze_generator import (
    Cell,
    MazeGenerator,
    DIRECTION_DELTA,
    DIRECTION_LETTER,
)


def solve_maze(
    gen: MazeGenerator,
    entry: tuple[int, int],
    exit_coord: tuple[int, int],
) -> Optional[list[str]]:
    """
    Find the shortest path using BFS (Breadth-First Search).

    BFS guarantees the minimum number of steps moving to a
    neighbour is only allowed when there is not wall
    between the two cells and the destination is not blocked.

    Returns:
        List of direction letters ['N','E','S','W'] describing the
        path, or None if no path exists.
    """
    grid = gen.get_maze()
    w, h = gen.width, gen.height

    # BFS queue: (current_position, accumulated_path)
    queue: deque[tuple[tuple[int, int], list[str]]] = deque()
    queue.append((entry, []))
    visited: set[tuple[int, int]] = {entry}

    while queue:
        (cx, cy), path = queue.popleft()

        if (cx, cy) == exit_coord:
            return path

        cell: Cell = grid[cy][cx]

        for direction, (dx, dy) in DIRECTION_DELTA.items():
            # Only move through OPEN walls
            if cell.has_wall(direction):
                continue

            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < w and 0 <= ny < h):
                continue

            nb = grid[ny][nx]
            if nb.is_blocked:
                continue

            pos = (nx, ny)
            if pos not in visited:
                visited.add(pos)
                queue.append((pos, path + [DIRECTION_LETTER[direction]]))

    return None  # No solution


def write_output(
    gen: MazeGenerator,
    entry: tuple[int, int],
    exit_coord: tuple[int, int],
    path: list[str],
    output_file: str,
) -> None:
    """
    Write the maze to the output file in hexadecimal format.
    """
    grid = gen.get_maze()

    with open(output_file, "w", encoding="utf-8") as f:
        # Maze rows
        for row in grid:
            f.write("".join(cell.to_hex() for cell in row) + "\n")

        # Separator
        f.write("\n")

        # Metadata
        f.write(f"{entry[0]},{entry[1]}\n")
        f.write(f"{exit_coord[0]},{exit_coord[1]}\n")
        f.write("".join(path) + "\n")
