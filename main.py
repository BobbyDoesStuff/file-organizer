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
from s3_uploader.s3_uploader import S3Uploader, setup_logging


def set_up_logger() -> None:
    """Sets up the program logger to record errors which occur at runtime."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler = logging.FileHandler(f"{__name__}.log")
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


@click.command()
@click.argument("source_directory", type=click.Path(exists=True))
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True),
    default=None,
    help="Configuration file path.",
)
def organize(source_directory: str, config: Optional[str]) -> None:
    """Organizes files in the specified source_directory."""
    if config is None:
        config = "config.json" if Path("config.json").exists() else None

    organizer = DataOrganizer(config)
    organizer.organize_files(source_directory)


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
    logger = setup_logging()
    uploader = S3Uploader(bucket_name)
    uploader.upload_directory(directory_path)


@click.group()
def cli():
    pass


cli.add_command(organize)
cli.add_command(generate)
cli.add_command(upload_to_s3)


if __name__ == "__main__":
    set_up_logger()
    cli()