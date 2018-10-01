import functools
import pathlib
import typing

import click
import click._termui_impl

from fidelius.incantations import NameIncantation
from fidelius.secrets import (
    EncryptableSecret, Fidelius, GPG, Secret, SecretKeeper)
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
    '-v', '--verbose', 'gpg_verbose',
    default=False,
    is_flag=True,
    help="Display GPG's normal STDERR output.")
@click.pass_context
def main(
        ctx,
        directory: pathlib.Path,
        gpg_verbose: bool):
    incantation = NameIncantation(directory)
    gpg = GPG(verbose=gpg_verbose)
    ctx.obj: SecretKeeper = Fidelius.cast(incantation=incantation, gpg=gpg)


@main.command()
@click.pass_obj
def ls(fidelius: SecretKeeper):
    """List all encrypted paths with their decrypted path."""
    for secret in fidelius:
        click.echo(f"{enc(secret)} -> {dec(secret)}")


@main.command()
@click.pass_obj
def ls_encrypted(sk: SecretKeeper):
    """List all encrypted files."""
    for secret in sk:
        click.echo(enc(secret))


@main.command()
@click.pass_obj
def ls_decrypted(sk: SecretKeeper):
    """List all decrypted files."""
    for secret in sk:
        click.echo(dec(secret))


@main.command()
@click.pass_obj
def decrypt(sk: SecretKeeper):
    """Decrypt all files."""
    for secret in sk:
        secret.decrypt()
        click.echo(f"Decrypted {enc(secret)} to {dec(secret)}")


@main.command()
@click.pass_obj
def clean(sk: SecretKeeper):
    """Delete all decrypted files."""
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
def cat(sk: SecretKeeper, encrypted_secret: pathlib.Path):
    """Read and print the contents of an encrypted file."""
    click.echo(sk[encrypted_secret].contents(), nl=False)


@main.command()
@click.argument(
    'encrypted_secret',
    type=PathType(exists=True),
    required=True)
@click.pass_obj
def view(sk: SecretKeeper, encrypted_secret: pathlib.Path):
    """View the decrypted text of an encrypted file in your $PAGER."""
    gpg_stdout = sk[encrypted_secret].stream()

    # Use the `click._termui_impl.pager()` method directly because
    # `click.echo_via_pager` appends a newline.
    click._termui_impl.pager(gpg_stdout)


@main.command()
@click.option(
    '-r', '--recipient', 'recipients',
    metavar='ID',
    envvar='FIDELIUS_RECIPIENTS',
    multiple=True,
    type=click.STRING,
    help="Forwarded directly to gpg --encrypt.")
@click.argument(
    'path',
    type=PathType(),
    required=True)
@click.pass_context
def edit(
        ctx,
        path: pathlib.Path,
        recipients: typing.Iterable[str]):
    """
    Edit an encrypted file.

    The $FIDELIUS_RECIPIENTS environment variable can be used to set a comma
    separated list of recipients GPG will encrypt the new contents for.
    """
    secret = ctx.obj.get(path, default=EncryptableSecret(path))

    text = click.edit(
        text=secret.contents(),
        extension=secret.contents_suffix())

    if not text:
        ctx.fail("Aborting as no changes were made")

    secret.write(text)

    path.write_text(ctx.obj.gpg.encrypt(text, recipients))