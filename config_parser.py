from dataclasses import dataclass
from typing import Optional


@dataclass
class MazeConfig:
    """
    It is a class that is used as container of values
    we don need to use self or nothing similar.
    """

    width: int
    height: int
    entry: tuple[int, int]
    exit: tuple[int, int]
    output_file: str
    perfect: bool
    seed: Optional[int] = None


class ConfigError(Exception):
    """Raised when the configuration file contains an error."""

    pass


def _parse_coords(value: str, key: str) -> tuple[int, int]:
    """
    converts the data of Entry and Exit since "0,0" to 0,0
    Returns:
        Tuple (x, y).

    Raises:
        ConfigError: Invalid format.
    """
    parts = value.split(",")
    if len(parts) != 2:
        raise ConfigError(
            f"{key}: expected 'x,y', got '{value}'"
        )
    try:
        return (int(parts[0].strip()), int(parts[1].strip()))
    except ValueError as exc:
        raise ConfigError(
            f"{key}: coordinates must be integers, got '{value}'"
        ) from exc


def _parse_bool(value: str, key: str) -> bool:
    """
    Parse a string into a boolean.

    It will accept the values: true, yes, 1, or false, no, 0
    and returns True or False

    Returns:
        A Boolean value than can be True or False

    if there is an error:
    Raises:
        ConfigError: Unrecognised value.
    """
    normalised = value.lower().strip()
    if normalised in ("true", "yes", "1"):
        return True
    if normalised in ("false", "no", "0"):
        return False
    raise ConfigError(
        f"{key}: invalid boolean '{value}' "
        "(use True/False, yes/no or 1/0)"
    )


def parse_config_file(filepath: str) -> MazeConfig:
    """
    Read and validate a configuration file.

    checks everything is fine and okay
    Returns:
        validated MazeConfig

    if there is an error:
        Raises:
        FileNotFoundError: The file does not exist.
        ConfigError: Format or validation error.
    """
    raw: dict[str, str] = {}

    with open(filepath, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                raise ConfigError(
                    f"Line {lineno}: missing '=' in '{line}'"
                )

            key, _, value = line.partition("=")
            key = key.strip().upper()
            value = value.strip()

            if not key or not value:
                raise ConfigError(
                    f"Line {lineno}: empty key or value in '{line}'"
                )

            raw[key] = value

    required = [
        "WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"
    ]
    missing = [k for k in required if k not in raw]
    if missing:
        raise ConfigError(
            "Missing required keys: " + ", ".join(missing)
        )

    try:
        width = int(raw["WIDTH"])
        height = int(raw["HEIGHT"])
    except ValueError as exc:
        raise ConfigError("WIDTH and HEIGHT must be integers") from exc

    entry = _parse_coords(raw["ENTRY"], "ENTRY")
    exit_coord = _parse_coords(raw["EXIT"], "EXIT")
    output_file = raw["OUTPUT_FILE"]
    perfect = _parse_bool(raw["PERFECT"], "PERFECT")

    # Optional SEED
    seed: Optional[int] = None
    if "SEED" in raw:
        try:
            seed = int(raw["SEED"])
        except ValueError as exc:
            raise ConfigError(
                f"SEED must be an integer, got '{raw['SEED']}'"
            ) from exc

    # Domain validation
    if width <= 0 or height <= 0:
        raise ConfigError("WIDTH and HEIGHT must be greater than 0")

    if entry == exit_coord:
        raise ConfigError("ENTRY and EXIT must be different")

    if not (0 <= entry[0] < width and 0 <= entry[1] < height):
        raise ConfigError(
            f"ENTRY {entry} is outside the maze ({width}x{height})"
        )

    if not (0 <= exit_coord[0] < width and 0 <= exit_coord[1] < height):
        raise ConfigError(
            f"EXIT {exit_coord} is outside the maze ({width}x{height})"
        )

    return MazeConfig(
        width=width,
        height=height,
        entry=entry,
        exit=exit_coord,
        output_file=output_file,
        perfect=perfect,
        seed=seed,
    )
