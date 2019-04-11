# -*- coding: utf-8 -*-

"""Console script for qi_irida_utils."""
import sys
import click
import download
import logging
import qc_check

logging.basicConfig()
log = logging.getLogger()


@click.group()
def cli1(args=None):
    pass


@cli1.command()
def download(args=None):
    """Console script for qi_irida_utils."""
    download.main()
    return 0


@cli1.command()
def sync_workflow(args=None):
    """Syncronise workflow between galaxy and local IRIDA environment"""
    click.echo("Not Implemented!")
    return 0


@cli1.command()
@click.option("--project", default="all", help="ID for project (or all)")
def qc(project):
    """QC Check for a given project"""
    qc_check.check(project)
    return 0


cli = click.CommandCollection(sources=[cli1])

if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
