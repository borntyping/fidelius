import functools
import pathlib

import click
import click._termui_impl

from fidelius.secrets import (Fidelius, Secret, SecretKeeper)
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


class PathType(click.Path):
    def convert(self, value, param, ctx):
        return pathlib.Path(super().convert(value, param, ctx))


@click.group(help=__doc__)
@click.option(
    '-d', '--directory',
    type=PathType(
        file_okay=False,
        dir_okay=True,
        exists=True),
    default=find_git_directory,
    help="Defaults to the current git repository.")
@click.option(
    '-G',
    '--no-gitignore',
    default=False,
    is_flag=True,
    help="Don't check decrypted files are ignored by git.")
@click.option(
    '-v', '--verbose', 'gpg_verbose',
    default=False,
    is_flag=True,
    help="Display GPG's normal STDERR output.")
@click.pass_context
def main(
        ctx,
        directory: pathlib.Path,
        gpg_verbose: bool,
        no_gitignore: bool,
):
    ctx.obj = SecretKeeper(
        secrets=Fidelius(directory).cast(),
        gpg_verbose=gpg_verbose)

    if not no_gitignore:
        ctx.obj.check_gitignore()


@main.command()
@click.pass_obj
def ls(sk: SecretKeeper):
    for secret in sk:
        click.echo(f"{enc(secret)} -> {dec(secret)}")


@main.command()
@click.pass_obj
def ls_encrypted(sk: SecretKeeper):
    for secret in sk:
        click.echo(enc(secret))


@main.command()
@click.pass_obj
def ls_decrypted(sk: SecretKeeper):
    for secret in sk:
        click.echo(dec(secret))


@main.command()
@click.pass_obj
def decrypt(sk: SecretKeeper):
    for secret in sk:
        click.echo(f"Decrypting {enc(secret)} to {dec(secret)}")
        sk.decrypt(secret)


@main.command()
@click.pass_obj
def clean(sk: SecretKeeper):
    for secret in sk:
        if secret.decrypted.exists():
            click.echo(f"Deleting {dec(secret)}")
            secret.decrypted.unlink()


@main.command()
@click.argument(
    'encrypted_secret',
    type=PathType(exists=True),
    required=True)
@click.pass_obj
def view(sk: SecretKeeper, encrypted_secret: pathlib.Path):
    """View the decrypted text of an encrypted file in your $PAGER."""
    gpg_stdout = sk.read(sk[encrypted_secret])

    # Use the `click._termui_impl.pager()` method directly because
    # `click.echo_via_pager` appends a newline.
    click._termui_impl.pager(gpg_stdout)
