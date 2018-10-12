"""
Each Incantation can be converted to a list of secrets.
"""

import pathlib
import typing

import attr

from .secrets import Secret
from .utils import in_directories


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
        directories = self.directories('**/*.encrypted*')

        for enc_dir in directories:
            dec_dir = self.rename_directory(enc_dir)
            for enc_path in enc_dir.glob('**/*'):
                if enc_path.is_file():
                    yield (enc_path, self.rename(self.transpose(
                        enc_path, from_dir=enc_dir, to_dir=dec_dir)))

        for enc_path in sorted(self.files('**/*.encrypted*')):
            if not in_directories(enc_path, directories):
                yield (enc_path, self.rename(enc_path))

    def directories(self, pattern: str) -> typing.Sequence[pathlib.Path]:
        """Find directories that match a pattern."""
        return tuple(sorted(
            path for path in self.directory.glob(pattern) if path.is_dir()))

    def files(self, pattern: str) -> typing.Sequence[pathlib.Path]:
        """Find our files that are not in the directories we already have."""
        return tuple(sorted(
            path for path in self.directory.glob(pattern) if path.is_file()))

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
