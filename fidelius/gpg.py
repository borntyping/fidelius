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
    home: typing.Optional[pathlib.Path] = attr.ib(default=None)

    def command(
            self,
            arguments: typing.Sequence[str],
            armour: bool) -> typing.Tuple[str, ...]:
        command: typing.Tuple[str, ...] = ('gpg', '--yes')
        if armour:
            command = (*command, '--armour')
        if self.verbose:
            command = (*command, '--verbose')
        return (*command, *arguments)

    def run(self,
            arguments: typing.Sequence[str],
            armour: bool,
            stdin: typing.Optional[str] = None) -> subprocess.CompletedProcess:
        env = {'GNUPGHOME': self.home.as_posix()} if self.home else {}
        try:
            return subprocess.run(
                self.command(arguments, armour),
                encoding='utf-8',
                input=stdin,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=True)
        except subprocess.CalledProcessError as error:
            for line in error.stderr.splitlines():
                log.error(line)
            raise

    def decrypt(
            self,
            encrypted: pathlib.Path,
            decrypted: pathlib.Path,
            armour: bool) -> subprocess.CompletedProcess:
        """Run an appropriate decryption method on the encrypted file."""
        log.debug(f"Decrypting {encrypted} to {decrypted}")

        if not decrypted.parent.exists():
            if self.parents:
                decrypted.parent.mkdir()
            else:
                raise FideliusException(
                    f"Directory {decrypted.parent} does not exist")

        return self.run([
            '--output', str(decrypted),
            '--decrypt', str(encrypted)
        ], armour=armour)

    def contents(self, path: pathlib.Path, armour: bool) -> str:
        log.debug("Reading contents of {path}")
        return self.run(['--decrypt', str(path)], armour).stdout

    def encrypt_text(
            self,
            path: pathlib.Path,
            text: str,
            armour: bool,
            recipients: typing.Iterable[str]) -> subprocess.CompletedProcess:
        log.debug(f"Encrypting {path}")
        args: typing.List[str] = []
        for recipient in recipients:
            args += ['--recipient', recipient]
        args += ['--output', str(path), '--encrypt']
        return self.run(args, armour=armour, stdin=text)

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
        self.run(args, armour)
