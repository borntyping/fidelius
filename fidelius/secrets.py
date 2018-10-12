import logging
import pathlib
import subprocess
import typing

import attr
import click

log = logging.getLogger(__name__)


class FideliusException(click.ClickException):
    pass


@attr.s(frozen=True)
class GPG:
    verbose: bool = attr.ib(default=False)
    parents: bool = attr.ib(default=True)

    def decrypt(
            self,
            encrypted: pathlib.Path,
            decrypted: pathlib.Path,
            armour: bool) -> None:
        """Run an appropriate decryption method on the encrypted file."""
        if not decrypted.parent.exists():
            if self.parents:
                decrypted.parent.mkdir()
            else:
                raise FideliusException(
                    f"Directory {decrypted.parent} does not exist")

        subprocess.run(
            self._gpg([
                '--output', str(decrypted),
                '--decrypt', str(encrypted)
            ], armour),
            encoding='utf-8',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE if not self.verbose else None)

    def contents(self, path: pathlib.Path, armour: bool) -> str:
        process = self._decrypt(path, armour)
        process.wait()
        return process.stdout.read()

    def stream(self, path: pathlib.Path, armour: bool):
        return self._decrypt(path, armour).stdout

    def _decrypt(self, path: pathlib.Path, armour: bool) -> subprocess.Popen:
        return subprocess.Popen(
            self._gpg(['--decrypt', str(path)], armour),
            encoding='utf-8',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE if not self.verbose else None)

    @staticmethod
    def _gpg(args: typing.Sequence[str], armour: bool) -> typing.Sequence[str]:
        command = ['gpg', '--yes']
        if armour:
            command += ['--armour']
        command += args
        return tuple(command)

    def encrypt_text(
            self,
            path: pathlib.Path,
            text: str,
            armour: bool,
            recipients):
        args = []
        for recipient in recipients:
            args += ['--recipient', recipient]
        args += ['--output', str(path), '--encrypt']
        subprocess.run(self._gpg(args, armour), encoding='utf-8', input=text)

    def encrypt_file(
            self,
            output: pathlib.Path,
            encrypt: pathlib.Path,
            armour: bool,
            recipients):
        args = []
        for recipient in recipients:
            args += ['--recipient', recipient]
        args += ['--output', str(output), '--encrypt', str(encrypt)]
        subprocess.run(self._gpg(args, armour), encoding='utf-8')


@attr.s(frozen=True, kw_only=True)
class Secret:
    encrypted: pathlib.Path = attr.ib()
    decrypted: pathlib.Path = attr.ib()

    def __attrs_post_init__(self):
        if self.encrypted.suffix not in ('.asc', '.gpg'):
            raise FideliusException(
                f"I don't know how to decrypt {self.encrypted.name}")

    @property
    def armour(self):
        return self.encrypted.suffix == '.asc'

    def decrypt(self, gpg: GPG):
        log.info(f"Decrypting {self.encrypted} to {self.encrypted}")
        return gpg.decrypt(self.encrypted, self.decrypted, self.armour)

    def re_encrypt(self, gpg: GPG, **kwargs):
        gpg.encrypt_file(
            output=self.encrypted,
            encrypt=self.decrypted,
            armour=self.armour,
            **kwargs)

    def stream(self, gpg: GPG):
        return gpg.stream(self.encrypted, self.armour)

    def contents(self, gpg: GPG):
        return gpg.contents(self.encrypted, self.armour)

    def plaintext(self):
        return self.decrypted.read_text()


@attr.s(frozen=True)
class SecretKeeper:
    secrets: typing.Dict[pathlib.Path, Secret] = attr.ib()
    gpg: GPG = attr.ib()

    def __getitem__(self, item: pathlib.Path):
        if item.resolve() not in self.secrets.keys():
            raise FideliusException(f"No secret named {item}")

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

    def decrypt(self):
        log.info(f"Decrypting {len(self.secrets)} secrets")
        for secret in self:
            secret.decrypt(self.gpg)
