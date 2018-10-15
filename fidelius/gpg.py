import logging
import pathlib
import subprocess
import typing

import attr

from .utils import FideliusException

log = logging.getLogger(__name__)


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
        log.debug(f"Decrypting {encrypted} to {decrypted}")

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
        log.debug("Reading contents of {path}")
        process = self._decrypt(path, armour)
        process.wait()
        return process.stdout.read()

    def stream(self, path: pathlib.Path, armour: bool):
        log.debug(f"Streaming {path}")
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
            recipients: typing.Iterable[str]):
        log.debug(f"Encrypting {path}")
        args: typing.List[str] = []
        for recipient in recipients:
            args += ['--recipient', recipient]
        args += ['--output', str(path), '--encrypt']
        subprocess.run(self._gpg(args, armour), encoding='utf-8', input=text)

    def encrypt_file(
            self,
            output: pathlib.Path,
            encrypt: pathlib.Path,
            armour: bool,
            recipients: typing.Iterable[str]):
        log.debug(f"Encrypting {encrypt} to {output}")
        args: typing.List[str] = []
        for recipient in recipients:
            args += ['--recipient', recipient]
        args += ['--output', str(output), '--encrypt', str(encrypt)]
        subprocess.run(self._gpg(args, armour), encoding='utf-8')
