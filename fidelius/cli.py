import functools
import pathlib
import typing

import click
import click._termui_impl

from . import __doc__
from fidelius.incantations import NameIncantation
from fidelius.secrets import Fidelius, GPG, Secret, SecretKeeper
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


def write_flags(func):
    recipients = click.option(
        '-r', '--recipient', 'recipients',
        metavar='ID',
        envvar='FIDELIUS_RECIPIENTS',
        multiple=True,
        type=click.STRING,
        help="Forwarded directly to gpg --encrypt.")

    path = click.argument(
        'path',
        type=PathType(),
        required=True)

    return recipients(path(func))


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
        secret.decrypt(sk.gpg)
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
    click.echo(sk[encrypted_secret].contents(sk.gpg), nl=False)


@main.command()
@click.argument(
    'encrypted_secret',
    type=PathType(exists=True),
    required=True)
@click.pass_obj
def view(sk: SecretKeeper, encrypted_secret: pathlib.Path):
    """View the decrypted text of an encrypted file in your $PAGER."""
    gpg_stdout = sk[encrypted_secret].stream(sk.gpg)

    # Use the `click._termui_impl.pager()` method directly because
    # `click.echo_via_pager` appends a newline.
    click._termui_impl.pager(gpg_stdout)


@main.command()
@write_flags
@click.pass_obj
def edit(
        sk: SecretKeeper,
        path: pathlib.Path,
        recipients: typing.Iterable[str]):
    """
    Edit an encrypted file.

    The $FIDELIUS_RECIPIENTS environment variable can be used to set a comma
    separated list of recipients GPG will encrypt the new contents for.
    """
    secret = sk[path]

    old_text = secret.contents(sk.gpg)

    new_text = click.edit(
        text=old_text,
        extension=secret.decrypted.suffix)

    if not new_text:
        raise click.ClickException("File is empty")

    if new_text == old_text:
        raise click.ClickException("No changes were made to the file")

    sk.gpg.encrypt(
        path=secret.encrypted,
        text=new_text,
        armour=secret.armour,
        recipients=recipients)


@main.command()
@write_flags
@click.pass_obj
def new(
        sk: SecretKeeper,
        path: pathlib.Path,
        recipients: typing.Iterable[str]):
    """
    Create an encrypted file.

    The $FIDELIUS_RECIPIENTS environment variable can be used to set a comma
    separated list of recipients GPG will encrypt the new contents for.
    """
    text = click.edit(extension=path.suffixes[-2])

    if not text:
        raise click.ClickException("New file is empty")

    sk.gpg.encrypt(
        path=path,
        text=text,
        armour=(path.suffix == '.asc'),
        recipients=recipients)
