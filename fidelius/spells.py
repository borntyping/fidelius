import pathlib

from .gpg import GPG
from .incantations import NameIncantation
from .secrets import SecretKeeper


def fidelius(directory: pathlib.Path, gpg: GPG = GPG()) -> SecretKeeper:
    return SecretKeeper(
        directory=directory,
        secrets=NameIncantation().secrets(directory),
        gpg=gpg)
