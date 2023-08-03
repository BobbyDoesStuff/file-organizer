"""
Main module of the program, responsible for
setting up the logger and acting as the starting point
of the program. Run this program with the required command
line arguments to achieve the implemented functionality.
"""
import logging
from typing import Optional

import click

from data_organizer.organizer import DataOrganizer


def set_up_logger() -> None:
    """
    Sets up the program logger to record
    errors which occur at runtime.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler = logging.FileHandler("data_organizer.log")
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


@click.command()
@click.argument("source_directory", type=click.Path(exists=True))
@click.option(
    "-c", "--config", type=click.Path(exists=True), help="Configuration file path."
)
def organize(source_directory: str, config: Optional[str]) -> None:
    """
    Key procedure - takes in the user arguments and
    organizes files in the specified source_directory.
    """
    organizer = DataOrganizer(config)
    organizer.organize_files(source_directory)


if __name__ == "__main__":
    set_up_logger()
    organize()
