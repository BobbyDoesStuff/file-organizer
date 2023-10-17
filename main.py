"""
Main module of the program, responsible for
 setting up the logger and acting as the 
 starting point of the program. 
 Run this program with the required 
 command line arguments to achieve 
 the implemented functionality.
"""

import logging
from pathlib import Path
from typing import Optional

import click

from data_organizer.organizer import DataOrganizer
from generate_terraform_script.generate_tf import TerraformGenerator
from logger.logger import default_logger as logger
from s3_uploader.s3_uploader import S3Uploader


@click.command()
@click.argument("source_directory", type=click.Path(exists=True))
@click.option(
    "-c",
    "--config",
    type=click.Path(),
    default=None,
    help="Configuration file path.",
)
def organize(source_directory: str, config: Optional[str]) -> None:
    """Organizes files in the specified source_directory."""
    if config:
        # Check if provided config exists
        if not Path(config).exists():
            err_msg = f"Error: The provided configuration file '{config}' does not exist."
            click.echo(err_msg)
            logger.error(err_msg)
            return
    else:
        config = "config.json" if Path("config.json").exists() else None
        if not config:
            err_msg = "Error: No configuration file found." \
                "Please provide one with --config option or have " \
                "a config.json in the current directory."
            click.echo(err_msg)
            logger.error(err_msg)
            return

    try:
        organizer = DataOrganizer(config)
        organizer.organize_files(source_directory)
    except Exception as e:
        click.echo(f"Error occurred while organizing the files: {str(e)}")
        logger.err(str(e))


@click.command()
@click.option(
    "--apply", is_flag=True, help="Apply the generated Terraform script."
)
def generate(apply: bool) -> None:
    """Generate a Terraform script based on .env configurations."""
    generator = TerraformGenerator()
    generator.generate_terraform_script()

    if apply:
        generator.apply_terraform()


@click.command()
@click.argument("bucket_name", type=str)
@click.argument("directory_path", type=click.Path(exists=True))
def upload_to_s3(bucket_name: str, directory_path: str) -> None:
    """Uploads the specified directory to the given S3 bucket."""
    # logger = setup_logging()
    uploader = S3Uploader(bucket_name)
    uploader.upload_directory(directory_path)


@click.group()
def cli():
    pass


cli.add_command(organize)
cli.add_command(generate)
cli.add_command(upload_to_s3)


if __name__ == "__main__":
    cli()
