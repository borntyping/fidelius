import logging
import os.path
import pathlib
import subprocess
import typing

import attr

from .utils import FideliusException
from .gpg import GPG

log = logging.getLogger(__name__)


@attr.s(frozen=True, kw_only=True)
class Secret:
    encrypted: pathlib.Path = attr.ib()
    decrypted: pathlib.Path = attr.ib()

    def __attrs_post_init__(self):
        if self.encrypted.suffix not in ('.asc', '.gpg'):
            raise FideliusException(
                f"I don't know how to decrypt {self.encrypted.name}")

    def __str__(self):
        return self.encrypted.name

    @property
    def armour(self):
        return self.encrypted.suffix == '.asc'

    def decrypt(self, gpg: GPG) -> None:
        log.debug(f"Decrypting {self.encrypted} to {self.encrypted}")
        gpg.decrypt(self.encrypted, self.decrypted, self.armour)

    def re_encrypt(self, gpg: GPG, **kwargs):
        log.debug(f"Re-encrypting {self.encrypted} from {self.decrypted}")
        gpg.encrypt_file(
            output=self.encrypted,
            encrypt=self.decrypted,
            armour=self.armour,
            **kwargs)

    def contents(self, gpg: GPG):
        log.debug(f"Reading contents of {self.encrypted}")
        return gpg.contents(self.encrypted, self.armour)

    def plaintext(self):
        log.debug(f"Reading contents of {self.decrypted}")
        return self.decrypted.read_text()


@attr.s(frozen=True)
class SecretKeeper:
    secrets: typing.Dict[pathlib.Path, Secret] = attr.ib()

    directory: pathlib.Path = attr.ib(factory=pathlib.Path.cwd)
    gpg: GPG = attr.ib(factory=GPG)

    def __getitem__(self, item: pathlib.Path):
        if item.resolve() not in self.secrets.keys():
            raise FideliusException(f"No secret named {item}")

        return self.secrets[item.resolve()]

    def rel(self, path: pathlib.Path) -> str:
        return os.path.relpath(path.as_posix(), self.directory.as_posix())

    def get(self, item: pathlib.Path, default: Secret) -> Secret:
        return self.secrets.get(item.resolve(), default)

    def __iter__(self):
        return iter(sorted(self.secrets.values(), key=lambda s: s.encrypted))

    def run_gitignore_check(self):
        log.info("Checking all decrypted files are ignored by git")
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
            log.info(f"Decrypting {self.rel(secret.encrypted)} "
                     f"to {self.rel(secret.decrypted)}")
            secret.decrypt(self.gpg)
        log.info(f"Decrypted {len(self.secrets)} secrets")
