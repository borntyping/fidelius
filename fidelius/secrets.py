import logging
import pathlib
import subprocess
import typing

import attr

from .incantations import Incantation

log = logging.getLogger(__name__)


class FideliusException(Exception):
    pass


@attr.s(frozen=True)
class GPG:
    verbose: bool = attr.ib(default=False)

    def decrypt(
            self,
            encrypted: pathlib.Path,
            decrypted: pathlib.Path,
            armour: bool) -> None:
        """Run an appropriate decryption method on the encrypted file."""
        self._run(['--output', str(decrypted),
                   '--decrypt', str(encrypted)], armour=armour)

    def contents(self, path: pathlib.Path, armour: bool) -> str:
        process = self._decrypt(path, armour)
        process.wait()
        return process.stdout.read()

    def stream(self, path: pathlib.Path, armour: bool):
        return self._decrypt(path, armour)

    def _decrypt(self, path: pathlib.Path, armour: bool) -> subprocess.Popen:
        return self._run(['--decrypt', str(path)], armour=armour)

    def _run(
            self,
            arguments: typing.Sequence[str],
            armour: bool,
            **kwargs) -> subprocess.Popen:
        command = ['gpg', '--yes']

        if armour:
            command += ['--armour']

        command += arguments

        return subprocess.Popen(
            command,
            encoding='utf-8',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE if not self.verbose else None,
            **kwargs)


@attr.s(frozen=True, kw_only=True)
class Secret:
    """An encrypted file we plan to decrypt."""

    encrypted: pathlib.Path = attr.ib()
    decrypted: pathlib.Path = attr.ib()

    gpg: GPG = attr.ib()

    def __attrs_post_init__(self):
        if self.encrypted.suffix not in ('.asc', '.gpg'):
            raise FideliusException(
                f"I don't know how to decrypt {self.encrypted.name}")

    @property
    def armour(self):
        return self.encrypted.suffix == '.asc'

    def decrypt(self):
        return self.gpg.decrypt(self.encrypted, self.decrypted, self.armour)

    def stream(self):
        return self.gpg.stream(self.encrypted, self.armour)

    def contents(self):
        return self.gpg.contents(self.encrypted, self.armour)


@attr.s(frozen=True)
class SecretKeeper:
    secrets: typing.Dict[pathlib.Path, Secret] = attr.ib()

    @classmethod
    def cast(cls, incantation: Incantation, gpg: GPG):
        return cls(secrets={secret.encrypted.resolve(): Secret(
            encrypted=secret.encrypted.resolve(),
            decrypted=secret.decrypted.resolve(),
            gpg=gpg
        ) for secret in incantation})

    def __attrs_post_init__(self):
        self.run_gitignore_check()

    def __getitem__(self, item: pathlib.Path):
        return self.secrets[item.resolve()]

    def __iter__(self):
        return iter(sorted(self.secrets.values(), key=lambda s: s.encrypted))

    def run_gitignore_check(self):
        decrypted = set(str(s.decrypted) for s in self.secrets.values())
        result = subprocess.run(
            ('git', 'check-ignore', '--stdin'),
            stdout=subprocess.PIPE,
            encoding='utf-8',
            input='\n'.join(decrypted))
        excluded = set(result.stdout.splitlines())
        included = decrypted - excluded
        if included:
            raise FideliusException(
                f"Encrypted file(s) not excluded by .gitignore: "
                f"{', '.join(sorted(included))}")


class Fidelius:
    @staticmethod
    def cast(incantation: Incantation, gpg: GPG) -> SecretKeeper:
        return SecretKeeper(secrets={
            encrypted.resolve(): Secret(
                encrypted=encrypted.resolve(),
                decrypted=decrypted.resolve(),
                gpg=gpg
            ) for encrypted, decrypted in incantation})
