import typing
from pathlib import Path

import git


def find_git_directory() -> typing.Optional[Path]:
    try:
        return Path(git.Repo(search_parent_directories=True).working_dir)
    except git.exc.InvalidGitRepositoryError:
        return None


def in_directory(
        file: Path,
        directory: Path) -> bool:
    """Check if a path is a subpath of a directory."""
    assert directory != file, f"Can't check {directory} is in itself"
    assert file.is_file(), f"Expected {file} to be a file"
    assert directory.is_dir(), f"Expected {directory} to be a directory"

    try:
        file.relative_to(directory)
    except ValueError:
        return False
    else:
        return True


def in_directories(
        path: Path,
        directories: typing.Sequence[Path]) -> bool:
    """Check if a path is a subpath of any of a list of directories."""
    return any(in_directory(path, directory) for directory in directories)
