import logging
import pathlib
import subprocess
import typing

import attr

from .utils import in_directories

log = logging.getLogger(__name__)


def run(command, **kwargs):
    return subprocess.check_call(command, **kwargs)


class FideliusException(Exception):
    pass


@attr.s(frozen=True)
class Secret:
    """An encrypted file we plan to decrypt."""

    encrypted: pathlib.Path = attr.ib()
    decrypted: pathlib.Path = attr.ib()

    def __attrs_post_init__(self):
        if self.encrypted.suffix not in ('.asc', '.gpg'):
            raise FideliusException(
                f"I don't know how to decrypt {self.encrypted.name}")

    @property
    def armour(self):
        return self.encrypted.suffix == '.asc'


@attr.s(frozen=True)
class SecretKeeper:
    gpg_verbose: bool = attr.ib()
    secrets: typing.Sequence[Secret] = attr.ib()

    def __iter__(self):
        return iter(self.secrets)

    def __getitem__(self, item: pathlib.Path):
        return self.secrets_map[item.resolve()]

    @property
    def secrets_map(self):
        return {s.encrypted.resolve(): s for s in self.secrets}

    def check_gitignore(self):
        decrypted = set((str(secret.decrypted) for secret in self.secrets))

        result = subprocess.run(
            ('git', 'check-ignore', '--stdin'),
            stdout=subprocess.PIPE,
            encoding='utf-8',
            input='\n'.join(decrypted))

        excluded = set(line.strip() for line in result.stdout.splitlines())

        included = decrypted - excluded

        if included:
            raise FideliusException(
                f"Encrypted file(s) not excluded by .gitignore: "
                f"{', '.join(sorted(included))}")

    def decrypt(self, secret: Secret):
        """Run an appropriate decryption method on the encrypted file."""
        return self._run(
            ['--output', str(secret.decrypted),
             '--decrypt', str(secret.encrypted)],
            armour=secret.armour)

    def read(self, secret: Secret):
        return self._run(
            ['--decrypt', str(secret.encrypted)],
            armour=secret.armour).stdout

    def _run(self, arguments: typing.Sequence[str], armour: bool, **kwargs):
        command = ['gpg', '--yes']

        if armour:
            command += ['--armour']

        command += arguments

        return subprocess.Popen(
            command,
            encoding='utf-8',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE if not self.gpg_verbose else None,
            **kwargs)


@attr.s(frozen=True)
class Fidelius:
    """Search for secrets to encrypt/decrypt in a directory."""

    git: pathlib.Path = attr.ib()

    def __attrs_post_init__(self):
        log.info(
            f"Searching for encrypted files and directories in {self.git}")

    def __iter__(self) -> Secret:
        directories = self.directories('**/*.encrypted*')

        for enc_dir in directories:
            dec_dir = self.rename_directory(enc_dir)
            for enc_path in enc_dir.glob('**/*'):
                yield Secret(enc_path, self.rename(self.transpose(
                    enc_path, from_dir=enc_dir, to_dir=dec_dir)))

        for enc_path in sorted(self.files('**/*.encrypted*')):
            if not in_directories(enc_path, directories):
                yield Secret(enc_path, self.rename(enc_path))

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

    def cast(self) -> typing.Sequence[Secret]:
        return list(self)
