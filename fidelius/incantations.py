"""
Each Incantation can be converted to a list of secrets.
"""

import pathlib
import typing

import attr

from .utils import in_directories


class Incantation:
    def __iter__(self):
        raise NotImplementedError


@attr.s(frozen=True)
class NameIncantation(Incantation):
    """
    Search for secrets to encrypt/decrypt in a directory.

    Selects files and directories with '.encrypted' in the name.
    """

    git: pathlib.Path = attr.ib()

    def __iter__(self):
        directories = self.directories('**/*.encrypted*')

        for enc_dir in directories:
            dec_dir = self.rename_directory(enc_dir)
            for enc_path in enc_dir.glob('**/*'):
                yield (enc_path, self.rename(self.transpose(
                    enc_path, from_dir=enc_dir, to_dir=dec_dir)))

        for enc_path in sorted(self.files('**/*.encrypted*')):
            if not in_directories(enc_path, directories):
                yield (enc_path, self.rename(enc_path))

    def directories(self, pattern: str) -> typing.Sequence[pathlib.Path]:
        """Find directories that match a pattern."""
        return tuple(sorted(p for p in self.git.glob(pattern) if p.is_dir()))

    def files(self, pattern: str) -> typing.Sequence[pathlib.Path]:
        """Find our files that are not in the directories we already have."""
        return tuple(sorted(p for p in self.git.glob(pattern) if p.is_file()))

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
