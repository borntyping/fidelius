import pathlib

from .secrets import Fidelius


def cast(directory: pathlib.Path) -> None:
    return Fidelius.quick(directory)
