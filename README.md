*This project has been created as part of the 42 curriculum by psanz-pe, pabserra.*

---

# A-Maze-ing

## Description

**A-Maze-ing** is a Python maze generator. Given a configuration file, it:

1. Generates a random maze using the **Recursive Backtracker (DFS)** algorithm.
2. Embeds a decorative **"42" pattern** of fully-walled cells.
3. Computes the **shortest path** between entry and exit (BFS).
4. Writes the result to a **hexadecimal output file**.
5. Opens an **interactive ASCII visualiser** in the terminal.

The maze can be **perfect** (exactly one path between any two cells) or
**imperfect** (extra passages, multiple routes).

---

## Instructions

### Requirements

- Python 3.10 or later
- Development dependencies: `flake8`, `mypy`, `build`

### Setup and execution

```bash
# Install development dependencies
make install

# Run with the default configuration
make run

# Run with a custom configuration file
python3 a_maze_ing.py my_config.txt

# Debug mode (opens pdb)
make debug

# Linting
make lint
make lint-strict    # optional, uses mypy --strict

# Remove caches
make clean
```

### Build the reusable package

```bash
make build
# Produces: mazegen_pkg/dist/mazegen-1.0.0-py3-none-any.whl
#           mazegen_pkg/dist/mazegen-1.0.0.tar.gz
```

---

## Configuration file format

The file contains `KEY=VALUE` pairs, one per line.
Lines starting with `#` are comments and are ignored.

| Key           | Description                                        | Example              | Required |
|---------------|----------------------------------------------------|----------------------|----------|
| `WIDTH`       | Maze width (number of columns)                     | `WIDTH=20`           | Yes      |
| `HEIGHT`      | Maze height (number of rows)                       | `HEIGHT=15`          | Yes      |
| `ENTRY`       | Entry coordinates `x,y`                            | `ENTRY=0,0`          | Yes      |
| `EXIT`        | Exit coordinates `x,y`                             | `EXIT=19,14`         | Yes      |
| `OUTPUT_FILE` | Path to the output file                            | `OUTPUT_FILE=maze.txt` | Yes    |
| `PERFECT`     | Perfect maze (`True`/`False`)                      | `PERFECT=True`       | Yes      |
| `SEED`        | Integer RNG seed for reproducibility               | `SEED=42`            | No       |

**Full example:**

```
# config.txt
WIDTH=20
HEIGHT=15
ENTRY=0,0
EXIT=19,14
OUTPUT_FILE=maze.txt
PERFECT=True
SEED=42
```

---

## Generation algorithm

The project uses **Recursive Backtracker** (iterative DFS with an explicit stack).

### Why this algorithm

- **Guarantees perfect mazes naturally.** The DFS visits each cell exactly once;
  on backtracking it never connects two already-visited branches.
  The result is a spanning tree of the cell graph — by definition a perfect maze.
- **Long winding corridors** give high visual complexity, ideal for puzzles.
- **Iterative implementation** (explicit stack) avoids Python's recursion limit
  on large mazes.
- **O(N) time and space** where N = number of free cells.

### Algorithm steps

1. Place the "42" pattern (blocked cells — ignored by the DFS).
2. Pick a random free starting cell.
3. While the stack is not empty:
   - If the current cell has unvisited free neighbours: pick one at random,
     remove the shared wall, mark it visited, push it onto the stack.
   - If no unvisited neighbours: pop (backtrack).
4. If `PERFECT=False`: remove ~5% of internal walls to add extra passages.

---

## Reusable module (`mazegen`)

The generation logic is packaged as `mazegen`, installable with `pip`
and importable in any Python 3.10+ project.

### Installation

```bash
pip install mazegen-1.0.0-py3-none-any.whl
```

### Basic usage

```python
from mazegen import MazeGenerator, solve_maze, Wall # need

gen = MazeGenerator(width=20, height=15, seed=42)  # need
gen.generate()                        # perfect=True by default  need

maze = gen.get_maze()                 # list[list[Cell]]  OPTIONAL
cell = gen.get_cell(0, 0)            # Cell at (col=0, row=0)  OPTIONAL
print(cell.to_hex())                  # e.g. "9"  OPTIONAL
print(cell.has_wall(Wall.NORTH))      # True if north wall is closed  OPTIONAL

path = solve_maze(gen, (0, 0), (19, 14))  # need
print("".join(path))                  # e.g. "SSEENE..."  OPTIONAL
```

### Custom parameters

```python
gen = MazeGenerator(
    width=30,
    height=20,
    seed=1234,        # None = different every time
    entry=(0, 0),
    exit=(29, 19),
)
gen.generate(perfect=False)
```

### Re-generating

```python
gen.reset()     # clears the grid, continues the internal RNG
gen.generate()  # produces a different maze
```

### Exported symbols

| Symbol            | Description                                       |
|-------------------|---------------------------------------------------|
| `MazeGenerator`   | Main generation class                             |
| `Cell`            | Individual cell with wall flags and helper methods|
| `Wall`            | IntFlag: NORTH=1 / EAST=2 / SOUTH=4 / WEST=8     |
| `solve_maze`      | BFS solver -> list of N/E/S/W letters, or None    |
| `DIRECTION_DELTA` | Dict Wall -> (dx, dy)                             |
| `DIRECTION_LETTER`| Dict Wall -> output-file letter                   |

---

## Interactive visualiser

When the program runs, the ASCII visualiser opens in the terminal:

```
==== A-Maze-ing ====
1. Re-generate a new maze
2. Show/Hide shortest path
3. Cycle wall colours
4. Quit
Choice (1-4):
```

- `EN` (bright magenta) marks the entry cell.
- `EX` (bright red) marks the exit cell.
- `42` (yellow) marks the decorative pattern cells.
- `··` (cyan) marks the shortest path when shown.
- Five colour presets cycle on option 3: White, Gold, Green, Cyan, Magenta.

---

## Resources

### Technical references

- Jamis Buck, *Mazes for Programmers* (Pragmatic Bookshelf, 2015) —
  the standard reference for maze generation algorithms.
- [Wikipedia: Maze generation algorithm](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- [Buckblog: Recursive Backtracker](https://weblog.jamisbuck.org/2010/12/27/maze-generation-recursive-backtracker)
- [Wikipedia: Spanning tree](https://en.wikipedia.org/wiki/Spanning_tree) —
  connection between perfect mazes and spanning trees.
- [Python docs: dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [Python docs: enum.IntFlag](https://docs.python.org/3/library/enum.html#intflag)
- [Python docs: collections.deque](https://docs.python.org/3/library/collections.html#collections.deque)

### AI usage

Claude (Anthropic) was used for:

- **Requirements review**: analysing the subject and identifying missing pieces
  (the `mazegen` package, the mypy return-type error, missing `SEED` in config).
- **Refactoring suggestions**: using a private `random.Random` instance instead
  of the global state, and how to structure `pyproject.toml`.
- **Debugging**: identifying the flake8 F401 cause and the missing return
  annotation caught by mypy.

All generated code was reviewed, understood and manually verified before use.

---

### Tool

- **flake8** and **mypy** for code quality.
- **build** (PEP 517) for packaging `mazegen`.
- **Claude** (Anthropic) for review and debugging (see Resources section).
