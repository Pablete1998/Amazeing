"""
ASCII terminal renderer for the maze.

Renders the maze using Unicode block characters and ANSI colours.
Provides an interactive menu with the actions required by the subject:
  1. Re-generate a new maze
  2. Show/Hide the shortest path
  3. Cycle wall colours
  4. Quit
"""

import sys
from typing import Optional

from maze_generator import MazeGenerator, Wall


RESET = "\033[0m"
BOLD = "\033[1m"

_BLK = "\033[40m"

COLOR_PRESETS: list[dict[str, str]] = [
    {"wall": "\033[37m", "floor": _BLK, "name": "White/Black"},
    {"wall": "\033[33m", "floor": _BLK, "name": "Gold/Black"},
    {"wall": "\033[32m", "floor": _BLK, "name": "Green/Black"},
    {"wall": "\033[36m", "floor": _BLK, "name": "Cyan/Black"},
    {"wall": "\033[35m", "floor": _BLK, "name": "Magenta/Black"},
]

COLOR_ENTRY = "\033[95m"    # bright magenta -> entry
COLOR_EXIT = "\033[91m"     # bright red     -> exit
COLOR_PATH = "\033[96m"     # cyan           -> path
COLOR_BLOCKED = "\033[93m"  # yellow         -> '42' pattern

WALL_CH = "\u2588\u2588"
FLOOR_CH = "  "
PATH_CH = "\u00b7\u00b7"
ENTRY_CH = "EN"
EXIT_CH = "EX"
BLOCKED_CH = "42"


def render_maze(
    gen: MazeGenerator,
    entry: tuple[int, int],
    exit_coord: tuple[int, int],
    path_cells: Optional[set[tuple[int, int]]] = None,
    color_idx: int = 0,
) -> str:
    """
    Build the ASCII representation of the maze as a string.
    Args:
        gen: Generator on which generate() has been called.
        entry: Entry coordinates
        exit_coord: Exit coordinates
        path_cells: Set of (x, y) cells to highlight, or None.
        color_idx: Index into COLOR_PRESETS.

    Returns:
        String ready to be printed with print().
    """
    grid = gen.get_maze()
    w, h = gen.width, gen.height
    preset = COLOR_PRESETS[color_idx % len(COLOR_PRESETS)]
    wc = preset["wall"]
    fc = preset["floor"]

    lines: list[str] = []

    for r in range(h):
        top = ""
        for c in range(w):
            cell = grid[r][c]
            top += wc + WALL_CH + RESET
            if cell.has_wall(Wall.NORTH):
                top += wc + WALL_CH + RESET
            else:
                top += fc + FLOOR_CH + RESET
        top += wc + WALL_CH + RESET
        lines.append(top)

        mid = ""
        for c in range(w):
            cell = grid[r][c]
            if cell.has_wall(Wall.WEST):
                mid += wc + WALL_CH + RESET
            else:
                mid += fc + FLOOR_CH + RESET

            pos = (c, r)
            if pos == entry:
                mid += COLOR_ENTRY + ENTRY_CH + RESET
            elif pos == exit_coord:
                mid += COLOR_EXIT + EXIT_CH + RESET
            elif cell.is_blocked:
                mid += COLOR_BLOCKED + BLOCKED_CH + RESET
            elif path_cells and pos in path_cells:
                mid += COLOR_PATH + PATH_CH + RESET
            else:
                mid += fc + FLOOR_CH + RESET

        last = grid[r][w - 1]
        if last.has_wall(Wall.EAST):
            mid += wc + WALL_CH + RESET
        else:
            mid += fc + FLOOR_CH + RESET
        lines.append(mid)

    bot = ""
    for c in range(w):
        bot += wc + WALL_CH + RESET
        cell = grid[h - 1][c]
        if cell.has_wall(Wall.SOUTH):
            bot += wc + WALL_CH + RESET
        else:
            bot += fc + FLOOR_CH + RESET
    bot += wc + WALL_CH + RESET
    lines.append(bot)

    return "\n".join(lines)


def path_to_cells(
    entry: tuple[int, int],
    path: list[str],
) -> set[tuple[int, int]]:
    """
    Convert a sequence of direction steps into the set of visited cells.
    Returns:
        Set of cells including entry and all steps.
    """
    delta: dict[str, tuple[int, int]] = {
        "N": (0, -1), "S": (0, 1),
        "E": (1, 0), "W": (-1, 0),
    }
    cells: set[tuple[int, int]] = {entry}
    cx, cy = entry
    for step in path:
        dx, dy = delta[step]
        cx, cy = cx + dx, cy + dy
        cells.add((cx, cy))
    return cells


def _clear() -> None:
    """Clear the terminal screen using ANSI escape codes."""
    print("\033[2J\033[H", end="")


def _menu() -> None:
    """Print the action menu."""
    print(f"\n{BOLD}==== A-Maze-ing ===={RESET}")
    print("1. Re-generate a new maze")
    print("2. Show/Hide shortest path")
    print("3. Cycle wall colours")
    print("4. Quit")
    print("Choice (1-4): ", end="", flush=True)


def run_interactive(
    gen: MazeGenerator,
    entry: tuple[int, int],
    exit_coord: tuple[int, int],
    path: list[str],
    perfect: bool,
) -> None:
    """
    Run the interactive visualiser loop.

    The menu repeats until the user chooses option 4 or presses Ctrl+C.

    On re-generate (option 1): gen.reset() + gen.generate() are called
    and the path is recalculated with BFS (solve_maze).  The new maze
    uses the same RNG state (continued from last call), so every
    re-generation produces a different maze.

    Args:
        gen: Generator on which generate() has been called.
        entry: Entry coordinates (x, y).
        exit_coord: Exit coordinates (x, y).
        path: Initial path already computed by solve_maze.
        perfect: Whether to generate a perfect maze on re-generation.
    """
    from maze_solver import solve_maze  # avoids circular

    show_path = False
    color_idx = 0
    current_path = path

    while True:
        _clear()
        pcells = path_to_cells(entry, current_path) if show_path else None
        print(render_maze(gen, entry, exit_coord, pcells, color_idx))
        _menu()

        choice = sys.stdin.readline().strip()

        if choice == "1":
            gen.reset()
            gen.generate(perfect=perfect)
            new_path = solve_maze(gen, entry, exit_coord)
            current_path = new_path if new_path is not None else []
            show_path = False

        elif choice == "2":
            show_path = not show_path

        elif choice == "3":
            color_idx = (color_idx + 1) % len(COLOR_PRESETS)
            print(f"  Colour: {COLOR_PRESETS[color_idx]['name']}")

        elif choice == "4":
            print("Goodbye!")
            break

        else:
            print("  Invalid option. Press Enter to continue.")
            sys.stdin.readline()
