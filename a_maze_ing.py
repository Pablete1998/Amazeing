"""
A-Maze-ing -- Main entry point.

Usage:
    python3 a_maze_ing.py config.txt

Flow:
    1. Parse the configuration file.
    2. Generate the maze (DFS + '42' pattern + optional seed).
    3. Solve with BFS -> shortest path.
    4. Write the hexadecimal output file.
    5. Launch the interactive ASCII visualiser.
"""

import sys

from config_parser import ConfigError, MazeConfig, parse_config_file
from maze_generator import MazeGenerator
from maze_renderer import run_interactive
from maze_solver import solve_maze, write_output


def main() -> int:
    """
    Main program function.

    Returns:
        0 on success, 1 on any error.
    """
    if len(sys.argv) != 2:
        print(
            "Usage: python3 a_maze_ing.py <config_file>",
            file=sys.stderr,
        )
        return 1

    config_path = sys.argv[1]

    try:
        config: MazeConfig = parse_config_file(config_path)
    except FileNotFoundError:
        print(
            f"Error: file not found: {config_path}",
            file=sys.stderr,
        )
        return 1
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    gen = MazeGenerator(
        width=config.width,
        height=config.height,
        seed=config.seed,
        entry=config.entry,
        exit=config.exit,
    )

    try:
        gen.generate(perfect=config.perfect)
    except Exception as exc:
        print(f"Error generating maze: {exc}", file=sys.stderr)
        return 1

    path = solve_maze(gen, config.entry, config.exit)

    if path is None:
        print(
            "Error: no path exists between entry and exit.",
            file=sys.stderr,
        )
        return 1

    try:
        write_output(
            gen, config.entry, config.exit, path, config.output_file
        )
        print(f"Maze saved to: {config.output_file}")
    except OSError as exc:
        print(f"Error writing file: {exc}", file=sys.stderr)
        return 1

    try:
        run_interactive(
            gen=gen,
            entry=config.entry,
            exit_coord=config.exit,
            path=path,
            perfect=config.perfect,
        )
    except KeyboardInterrupt:
        print("\nInterrupted by user.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
