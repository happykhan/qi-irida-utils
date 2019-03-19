# -*- coding: utf-8 -*-

"""Console script for qi_irida_utils."""
import sys
import click
import os
from irida_workflow import prepare_sample
from basemount_sync import basemount
import logging

logging.basicConfig()
log = logging.getLogger()


@click.group()
def cli1(args=None):
    pass


@cli1.command()
@click.option(
    "--aspera_path",
    default=os.path.join(os.path.expanduser("~"), ".aspera/connect/bin/"),
    help="Path of ascp binary",
)
@click.option(
    "--fastqdump_path",
    default=os.path.join(os.path.expanduser("~"), "app/sratoolkit/bin/"),
    help="Path of fastq-dump binary",
)
@click.option(
    "--aspera_key",
    default=os.path.join(
        os.path.expanduser("~"), ".aspera/connect/etc/asperaweb_id_dsa.openssh"
    ),
    help="Path of ascp key",
)
@click.option(
    "--sample_file",
    default=os.path.join(os.path.expanduser("~"), "test_file.csv"),
    help="Path of sample file",
)
@click.option("--output_dir", default="/tmp/irwork", help="Output directory")
@click.option("--verbose", default=True, help="Verbose output")
def upload(aspera_path, fastqdump_path, aspera_key, sample_file, output_dir, verbose):
    """Uploads sequencing data (SRA or local) to IRIDA"""
    if verbose:
        log.setLevel(logging.DEBUG)
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    prepare_sample(sample_file, aspera_path, aspera_key, fastqdump_path, output_dir)
    return 0


@cli1.command()
def download(args=None):
    """Console script for qi_irida_utils."""
    click.echo("Not Implemented!")
    return 0


@cli1.command()
@click.option("--read_dir", default="/usr/users/QIB_fr005/alikhan/seq/Projects", help="Basemount directory")
@click.option("--verbose", default=True, help="Verbose output")
def basemount(read_dir, verbose):
    """Console script for qi_irida_utils."""
    if verbose:
        log.setLevel(logging.DEBUG)
    basemount(read_dir)
    return 0


@cli1.command()
def sync_workflow(args=None):
    """Syncronise workflow between galaxy and local IRIDA environment"""
    click.echo("Not Implemented!")
    return 0


cli = click.CommandCollection(sources=[cli1])

if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
