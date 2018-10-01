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
    recipients: typing.Tuple[str, ...] = attr.ib(factory=tuple)
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
        return subprocess.Popen(
            self._command(*arguments, armour=armour),
            encoding='utf-8',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE if not self.verbose else None,
            **kwargs)

    @staticmethod
    def _command(*arguments: str, armour: bool):
        command = ['gpg', '--yes']
        if armour:
            command += ['--armour']
        command += arguments
        return command

    def encrypt(
            self,
            path: pathlib.Path,
            text: str,
            armour: bool,
            recipients):
        arguments = []
        for recipient in recipients:
            arguments += ['--recipient', recipient]
        arguments += ['--encrypt', str(path)]

        subprocess.check_call(
            self._command(arguments, armour=armour),
            input=text)


@attr.s(frozen=True, kw_only=True)
class Secret:
    encrypted: pathlib.Path = attr.ib()
    gpg: GPG = attr.ib()

    def __attrs_post_init__(self):
        if self.encrypted.suffix not in ('.asc', '.gpg'):
            raise FideliusException(
                f"I don't know how to decrypt {self.encrypted.name}")

    @property
    def armour(self):
        return self.encrypted.suffix == '.asc'

    def contents(self) -> typing.Optional[str]:
        raise NotImplementedError

    def contents_suffix(self) -> str:
        raise NotImplementedError

    def write(self, text: str, recipients) -> None:
        self.gpg.encrypt(
            path=self.encrypted,
            text=text,
            armour=self.armour,
            recipients=recipients)


@attr.s(frozen=True, kw_only=True)
class EncryptableSecret(Secret):
    encrypted: pathlib.Path = attr.ib()
    gpg: GPG = attr.ib()

    def contents(self):
        return None

    def contents_suffix(self):
        return self.encrypted.suffixes[-2]


@attr.s(frozen=True, kw_only=True)
class DecryptableSecret(Secret):
    encrypted: pathlib.Path = attr.ib()
    decrypted: pathlib.Path = attr.ib()
    gpg: GPG = attr.ib()

    def decrypt(self):
        return self.gpg.decrypt(self.encrypted, self.decrypted, self.armour)

    def stream(self):
        return self.gpg.stream(self.encrypted, self.armour)

    def contents(self):
        return self.gpg.contents(self.encrypted, self.armour)

    def contents_suffix(self):
        return self.decrypted.suffix

    def write(self, text: str) -> None:
        pass


@attr.s(frozen=True)
class SecretKeeper:
    secrets: typing.Dict[pathlib.Path, Secret] = attr.ib()

    def __attrs_post_init__(self):
        self.run_gitignore_check()

    def __getitem__(self, item: pathlib.Path):
        return self.secrets[item.resolve()]

    def get(self, item: pathlib.Path, default: Secret) -> Secret:
        return self.secrets.get(item.resolve(), default)

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
            encrypted.resolve(): DecryptableSecret(
                encrypted=encrypted.resolve(),
                decrypted=decrypted.resolve(),
                gpg=gpg
            ) for encrypted, decrypted in incantation})
