import functools
import logging
import os.path
import pathlib
import typing

import click
import click._termui_impl

from . import __doc__, __version__
from .gpg import GPG
from .incantations import Fidelius
from .secrets import Secret, SecretKeeper
from .utils import find_git_directory

log = logging.getLogger(__name__)


@functools.lru_cache()
def rel(path: pathlib.Path) -> str:
    """
    Convert a path to a relative Path.

    Returns a string as these should only be used for presentation.
    """
    return os.path.relpath(path.as_posix(), pathlib.Path.cwd().as_posix())


def enc(secret: Secret) -> str:
    """Style a path to a encrypted file."""
    return click.style(rel(secret.encrypted), fg='green')


def dec(secret: Secret) -> str:
    """Style a path to a decrypted file."""
    return click.style(rel(secret.decrypted), fg='red')


class PathType(click.Path):
    def convert(self, value, param, ctx):
        return pathlib.Path(super().convert(value, param, ctx))


recipients_option = click.option(
    '-r', '--recipient', 'recipients',
    metavar='ID',
    envvar='FIDELIUS_RECIPIENTS',
    multiple=True,
    required=True,
    type=click.STRING,
    help="Forwarded directly to gpg --encrypt.")

secret_path_options = click.argument(
    'path',
    type=PathType(),
    required=True)

secrets_argument = click.argument(
    'secrets',
    type=PathType(),
    required=True,
    nargs=-1)


@click.group(help=__doc__)
@click.option(
    '-p', '--path',
    type=PathType(
        file_okay=False,
        dir_okay=True,
        exists=True),
    default=find_git_directory,
    required=True,
    help="Defaults to the current git repository.")
@click.option(
    '-d', '--debug', 'debug',
    default=False,
    is_flag=True,
    help="Enable debug logging.")
@click.option(
    '-v', '--verbose', 'gpg_verbose',
    default=False,
    is_flag=True,
    help="Display GPG's normal STDERR output.")
@click.pass_context
def main(
        ctx,
        debug: bool,
        path: pathlib.Path,
        gpg_verbose: bool):
    logging.basicConfig(level=(logging.DEBUG if debug else logging.WARNING))
    ctx.obj = Fidelius(path).cast(gpg=GPG(verbose=gpg_verbose))
    ctx.obj.run_gitignore_check()


@main.command()
def version():
    """Show the application version."""
    click.echo(f"fidelius {__version__}")


@main.command()
@click.pass_obj
def ls(sk: SecretKeeper):
    """List all encrypted paths with their decrypted path."""
    for secret in sk:
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
@click.argument(
    'secrets',
    type=PathType(),
    required=False,
    nargs=-1)
@click.pass_obj
def decrypt(sk: SecretKeeper, secrets: typing.Sequence[pathlib.Path]):
    """
    Create decrypted plaintext from encrypted secrets.

    If not paths are provides, decrypts all secrets.
    """
    selected: typing.List[Secret] = [sk[path] for path in secrets] if secrets else list(sk.secrets)

    for secret in selected:
        secret.decrypt(sk.gpg)
        click.echo(f"Decrypted {enc(secret)} to {dec(secret)}")


@main.command()
@click.pass_obj
def clean(sk: SecretKeeper):
    """Delete all decrypted plaintext files."""
    for secret in sk:
        if secret.decrypted.exists():
            click.echo(f"Deleting {dec(secret)}")
            secret.decrypted.unlink()


@main.command()
@secrets_argument
@click.pass_obj
def cat(sk: SecretKeeper, secrets: typing.Sequence[pathlib.Path]):
    """Print the contents of an encrypted file."""
    for secret in secrets:
        click.echo(sk[secret].contents(sk.gpg), nl=False)


@main.command()
@click.argument(
    'encrypted_secret',
    type=PathType(exists=True),
    required=True)
@click.pass_obj
def view(sk: SecretKeeper, encrypted_secret: pathlib.Path):
    """View the decrypted text of an encrypted file in your $PAGER."""
    contents = sk[encrypted_secret].contents(sk.gpg)

    # Use the `click._termui_impl.pager()` method directly because
    # `click.echo_via_pager` appends a newline.
    click._termui_impl.pager(contents)  # type: ignore


@main.command()
@recipients_option
@secret_path_options
@click.pass_obj
def edit(
        sk: SecretKeeper,
        path: pathlib.Path,
        recipients: typing.Iterable[str]):
    """
    Edit an encrypted file without creating decrypted plaintext.

    The $FIDELIUS_RECIPIENTS environment variable should be a whitespace
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

    sk.gpg.encrypt_text(
        path=secret.encrypted,
        text=new_text,
        armour=secret.armour,
        recipients=recipients)

    if secret.decrypted.exists():
        click.secho(
            f"Decrypted plaintext {secret.decrypted} is out of date - "
            f"run 'fidelius decrypt' to update it or 'fidelius clean' to remove it",
            fg='yellow')


@main.command(name='encrypt')
@recipients_option
@secrets_argument
@click.option(
    '--force/--no-force',
    default=False,
    help='Re-encrypt secrets when their contents are unchanged.')
@click.pass_obj
def encrypt(
        sk: SecretKeeper,
        secrets: typing.Sequence[pathlib.Path],
        recipients: typing.Iterable[str],
        force: bool):
    """
    Create encrypted secrets from decrypted plaintext.

    The $FIDELIUS_RECIPIENTS environment variable should be a whitespace
    separated list of recipients GPG will encrypt the new contents for.
    """
    for path in secrets:
        secret: Secret = sk[path]

        if not secret.decrypted.exists():
            click.echo(f"Plaintext for {enc(secret)} does not exist")
            continue

        if not force and secret.plaintext() == secret.contents(sk.gpg):
            click.echo(f"Skipping {enc(secret)} as no changes have been made "
                       f"in {dec(secret)}")
            continue

        secret.re_encrypt(sk.gpg, recipients=recipients)
        click.echo(f"Encrypted {enc(secret)} from the plaintext in {dec(secret)}")


@main.command()
@recipients_option
@secret_path_options
@click.argument(
    'plaintext', type=PathType(exists=True), default=None, required=False)
@click.pass_obj
def create(
        sk: SecretKeeper,
        path: pathlib.Path,
        plaintext: pathlib.Path,
        recipients: typing.Iterable[str]):
    """
    Create a new encrypted secret from a file.

    Paths should match one of the following forms:

    \b
        {directory}.encrypted/{name}.{ext}.{asc|gpg}
        {directory}.encrypted/{name}.encrypted.{ext}.{asc|gpg}
        {name}.encrypted.{ext}.{asc|gpg}

    The $FIDELIUS_RECIPIENTS environment variable should be a whitespace
    separated list of recipients GPG will encrypt the new contents for.
    """
    if len(path.suffixes) < 2 or path.suffix not in {'asc', 'gpg'}:
        raise click.ClickException(
            "File names should be in the form '<name>.<ext>.<asc|gpg>' or "
            "'<name>.encrypted.<ext>.<asc|gpg>'.")

    if not any('encrypted' in part for part in path.parts):
        raise click.ClickException(
            "File names should be in the form '<name>.encrypted.<ext>[.<asc|gpg>]' "
            "or be in a directory named in the form '<name>.encrypted/'.")

    if plaintext:
        sk.gpg.encrypt_file(
            output=path,
            encrypt=plaintext,
            armour=(path.suffix == '.asc'),
            recipients=recipients)
    else:
        text = click.edit(extension=path.suffixes[-2])
        if not text:
            raise click.ClickException("New file is empty")
        sk.gpg.encrypt_text(
            path=path,
            text=text,
            armour=(path.suffix == '.asc'),
            recipients=recipients)
