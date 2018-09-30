import click

from . import __doc__


@click.group(help=__doc__)
def main():
    pass


if __name__ == '__main__':
    main(prog_name='fidelius')
