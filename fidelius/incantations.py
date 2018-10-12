"""
Each Incantation can be converted to a list of secrets.
"""

import logging
import pathlib
import typing

import attr

from .secrets import Secret
from .utils import in_directories

log = logging.getLogger(__name__)


@attr.s(frozen=True)
class Incantation:
    directory: pathlib.Path = attr.ib()

    def __iter__(self):
        raise NotImplementedError

    @classmethod
    def secrets(
            cls,
            directory: pathlib.Path) -> typing.Dict[pathlib.Path, Secret]:
        return {encrypted.resolve(): Secret(
            encrypted=encrypted.resolve(),
            decrypted=decrypted.resolve(),
        ) for encrypted, decrypted in cls(directory)}


class NameIncantation(Incantation):
    """
    Search for secrets to encrypt/decrypt in a directory.

    Selects files and directories with '.encrypted' in the name.
    """

    def __iter__(self):
        log.info(f"Searching for encrypted files in {self.directory}")

        directories = self.directories(self.directory, '**/*.encrypted*')
        log.info(f"Found {len(directories)} encrypted directories")

        for enc_dir in sorted(directories):
            dec_dir = self.rename_directory(enc_dir)
            for enc_path in enc_dir.glob('**/*'):
                if enc_path.is_file():
                    yield (enc_path, self.rename(self.transpose(
                        enc_path, from_dir=enc_dir, to_dir=dec_dir)))

        files = [f for f in self.files(self.directory, '**/*.encrypted*')
                 if not in_directories(f, directories)]
        log.info(f"Found {len(files)} encrypted files")

        for enc_path in sorted(files):
            yield (enc_path, self.rename(enc_path))

    @staticmethod
    def directories(
            directory: pathlib.Path,
            pattern: str) -> typing.Sequence[pathlib.Path]:
        """Find directories that match a pattern."""
        return tuple(sorted(p for p in directory.glob(pattern) if p.is_dir()))

    @staticmethod
    def files(
            directory: pathlib.Path,
            pattern: str) -> typing.Sequence[pathlib.Path]:
        """Find our files that are not in the directories we already have."""
        return tuple(sorted(p for p in directory.glob(pattern) if p.is_file()))

    @staticmethod
    def rename_directory(path: pathlib.Path) -> pathlib.Path:
        """
        Modify the name of a directory, removing '.encrypted'.
        """
        return path.with_name(path.name.replace('.encrypted', ''))

    @staticmethod
    def rename(path: pathlib.Path) -> pathlib.Path:
        """
        Modify the name of a path, replacing '.encrypted' with '.decrypted'
        and removing the suffix of the file.
        """
        name = path.name.replace('.encrypted', '.decrypted')
        path = path.with_name(name).with_suffix('')

        if '.decrypted' not in path.suffixes:
            path = path.with_suffix(f'.decrypted{path.suffix}')

        return path

    @staticmethod
    def transpose(
            path: pathlib.Path, *,
            from_dir: pathlib.Path,
            to_dir: pathlib.Path) -> pathlib.Path:
        return to_dir / path.relative_to(from_dir)
