# -*- coding: utf-8 -*-

"""Console script for qi_irida_utils."""
import sys
import click


@click.command()
def main(args=None):
    """Console script for qi_irida_utils."""
    click.echo("Replace this message by putting your code into "
               "qi_irida_utils.cli.main")
    click.echo("See click documentation at http://click.pocoo.org/")
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
