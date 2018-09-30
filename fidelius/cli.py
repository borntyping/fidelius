import functools
import pathlib

import click

from fidelius.secrets import Fidelius, Secret, SecretKeeper


@functools.lru_cache()
def rel(path: pathlib.Path) -> str:
    return str(path.relative_to(pathlib.Path.cwd()))


def enc(secret: Secret) -> str:
    return click.style(rel(secret.encrypted), fg='green')


def dec(secret: Secret) -> str:
    return click.style(rel(secret.decrypted), fg='red')


def secrets(func):
    @click.pass_obj
    @functools.wraps(func)
    def wrapper(sk: SecretKeeper):
        for secret in sk:
            func(secret)

    return wrapper


@click.group(help=__doc__)
@click.option(
    '-g',
    '--no-check-gitignore/--check-gitignore',
    default=False,
    is_flag=True)
@click.pass_context
def main(ctx, no_check_gitignore: bool):
    ctx.obj: SecretKeeper = Fidelius().cast()

    if no_check_gitignore:
        ctx.obj.check_gitignore()


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
def list_(secret: Secret):
    click.echo(f"File {enc(secret)} will be decrypted to {dec(secret)}")


@main.command()
@secrets
def decrypt(secret: Secret):
    click.echo(f"Decrypting {enc(secret)} to {dec(secret)}")
    secret.decrypt()
