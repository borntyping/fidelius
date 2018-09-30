import functools
import pathlib

import click

from fidelius.secrets import Fidelius, Secret, SecretKeeper
from fidelius.utils import find_git_directory


@functools.lru_cache()
def rel(path: pathlib.Path) -> str:
    """
    Convert a path to a relative Path.

    Returns a string as these should only be used for presentation.
    """
    return str(path.relative_to(pathlib.Path.cwd()))


def enc(secret: Secret) -> str:
    """Style a path to a encrypted file."""
    return click.style(rel(secret.encrypted), fg='green')


def dec(secret: Secret) -> str:
    """Style a path to a decrypted file."""
    return click.style(rel(secret.decrypted), fg='red')


def secrets(func):
    """Run a CLI command once for each Secret in a SecretKeeper."""

    @click.pass_obj
    @functools.wraps(func)
    def wrapper(sk: SecretKeeper, **kwargs):
        for secret in sk:
            func(secret, **kwargs)

    return wrapper


def click_convert_path(_ctx, _param, value) -> pathlib.Path:
    return pathlib.Path(value)


@click.group(help=__doc__)
@click.option(
    '-d', '--directory',
    type=click.Path(
        file_okay=False,
        dir_okay=True,
        exists=True),
    callback=click_convert_path,
    default=find_git_directory)
@click.option(
    '-g',
    '--no-check-gitignore/--check-gitignore',
    default=False,
    is_flag=True)
@click.pass_context
def main(ctx, directory: pathlib.Path, no_check_gitignore: bool):
    ctx.obj: SecretKeeper = Fidelius(directory).cast()

    if no_check_gitignore:
        ctx.obj.check_gitignore()


@main.command()
@secrets
def ls(secret: Secret):
    click.echo(f"{enc(secret)} -> {dec(secret)}")


@main.command()
@secrets
def ls_encrypted(secret: Secret):
    click.echo(enc(secret))


@main.command()
@secrets
def ls_decrypted(secret: Secret):
    click.echo(dec(secret))


@main.command()
@secrets
def clean(secret: Secret):
    if secret.decrypted.exists():
        click.echo(f"Deleting {dec(secret)}")
        secret.decrypted.unlink()


@main.command()
@click.option(
    '-v', '--verbose/--no-verbose',
    default=False,
    is_flag=True,
    help="Display GPG output.")
@secrets
def decrypt(secret: Secret, verbose: bool):
    click.echo(f"Decrypting {enc(secret)} to {dec(secret)}")
    secret.decrypt(verbose=verbose)
