import pathlib

from .incantations import NameIncantation
from .secrets import GPG, SecretKeeper


def fidelius(directory: pathlib.Path, gpg: GPG = GPG()) -> SecretKeeper:
    return SecretKeeper(secrets=NameIncantation.secrets(directory), gpg=gpg)
