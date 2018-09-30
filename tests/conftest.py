import pathlib

import attr
import click.testing
import pytest

import fidelius.cli

ROOT = pathlib.Path(__file__).parent


@pytest.fixture()
def invoke():
    def invoke_func(arguments):
        runner = click.testing.CliRunner()
        result = runner.invoke(fidelius.cli.main, arguments)
        assert result.exit_code == 0, f"Command failed: \n\n{result.output}"
        return result.output.splitlines()

    return invoke_func


@attr.s(frozen=True)
class ExampleSecret:
    name: str = attr.ib()
    encrypted: pathlib.Path = attr.ib()
    decrypted: pathlib.Path = attr.ib()

    def __str__(self):
        return self.name

    @property
    def enc(self):
        return fidelius.cli.rel(self.encrypted)

    @property
    def dec(self):
        return fidelius.cli.rel(self.decrypted)


@pytest.fixture(params=[
    ExampleSecret(
        'file-asc',
        ROOT / 'files/file-asc.encrypted.json.asc',
        ROOT / 'files/file-asc.decrypted.json',
    ),
    ExampleSecret(
        'file-gpg',
        ROOT / 'files/file-gpg.encrypted.json.gpg',
        ROOT / 'files/file-gpg.decrypted.json',
    ),
    ExampleSecret(
        'dir-asc-short',
        ROOT / 'files.encrypted/dir-asc-short.json.asc',
        ROOT / 'files/dir-asc-short.decrypted.json',
    ),
    ExampleSecret(
        'dir-gpg-short',
        ROOT / 'files.encrypted/dir-gpg-short.json.gpg',
        ROOT / 'files/dir-gpg-short.decrypted.json',
    ),
    ExampleSecret(
        'dir-asc-long',
        ROOT / 'files.encrypted/dir-asc-long.encrypted.json.asc',
        ROOT / 'files/dir-asc-long.decrypted.json',
    ),
    ExampleSecret(
        'dir-gpg-long',
        ROOT / 'files.encrypted/dir-gpg-long.encrypted.json.gpg',
        ROOT / 'files/dir-gpg-long.decrypted.json',
    )
], ids=str)
def secret(request):
    return request.param
