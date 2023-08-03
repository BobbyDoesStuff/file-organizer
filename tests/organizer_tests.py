"""
Performs automated tests on the data organizer,
including random tests to ensure the program works robustly.
"""
import random
import string
import sys
from pathlib import Path
from typing import Optional

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_organizer.organizer import DataOrganizer


@pytest.fixture
def mock_config() -> dict:
    """Define the mock configuration for testing."""
    return {
        "directories": {"media": "media", "documents": "documents", "other": "other"},
        "file_types": {
            "media": ["jpg", "jpeg", "png", "mp4", "avi"],
            "documents": ["pdf", "docx", "xlsx"],
            "other": ["*"],
        },
    }


# Keep the source directory the same for all tests that need it.
SOURCE_DIRECTORY = Path("/path/to/source")
# Defines possible file name characters for random file name generation.
POSSIBLE_FILENAME_CHARACTERS = f"{string.ascii_letters}{string.digits}."


def create_data_organizer_with_config(mock_config: dict) -> DataOrganizer:
    """Returns a DataOrganizer object with configration set."""
    data_organizer = DataOrganizer()
    data_organizer.directories = mock_config.get("directories", {})
    data_organizer.file_types = mock_config.get("file_types", {})
    data_organizer.ignore_list = mock_config.get("ignore_list", [])
    return data_organizer


def generate_random_file_name(
    extensions: Optional[list] = None, exclude_extensions: Optional[list] = None
) -> str:
    """
    Generates a random file name based on given extensions
    whilst avoiding certain extensions if indicated.
    """
    if extensions is None:
        extensions = []
    if exclude_extensions is None:
        exclude_extensions = []
    # Filter out any extensions to exclude.
    extensions = [
        extension for extension in extensions if extension not in exclude_extensions
    ]
    # Determines the random length of the filename part before the extension.
    prefix_length = random.randint(1, 32)
    # Generates the prefix string.
    prefix = "".join(random.choices(POSSIBLE_FILENAME_CHARACTERS, k=prefix_length))
    if extensions:
        # Simply chooses a random set extension.
        extension = random.choice(extensions)
    else:
        # No extensions to choose from,
        # generate a completely random one instead.
        extension_length = random.randint(1, 5)
        extension = "".join(
            random.choices(POSSIBLE_FILENAME_CHARACTERS, k=extension_length)
        )
        while extension in exclude_extensions:
            # Generate a new extension if the generated extension is
            # a part of 'exclude_extensions'.
            extension = "".join(
                random.choices(POSSIBLE_FILENAME_CHARACTERS), k=extension_length
            )
    # Joins the file prefix and extension, separated by a period,
    # and returns the file name.
    return f"{prefix}.{extension}"


def test_get_destination_path_with_known_file_type(mock_config: dict) -> None:
    """Tests files of a known type get moved into the set folder."""
    data_organizer = create_data_organizer_with_config(mock_config)
    file_types = mock_config["file_types"]["media"]

    for _ in range(100):
        file_name = generate_random_file_name(file_types)
        # Also prove lots of sub-directories works no problem.
        file_path = SOURCE_DIRECTORY / "a" / "b" / "c" / file_name
        # Act
        dest_path = data_organizer.get_destination_path(SOURCE_DIRECTORY, file_path)
        # Assert
        assert dest_path == SOURCE_DIRECTORY / "media" / file_path.name


def test_get_destination_path_with_unknown_file_type(mock_config: dict) -> None:
    """Tests files of an unknown type get moved into the 'other' folder."""
    data_organizer = create_data_organizer_with_config(mock_config)
    # Do not generate any of the known file types.
    exclude = []
    for key, file_types in mock_config["file_types"].items():
        if key == "other":
            continue
        exclude.extend(file_types)

    for _ in range(100):
        file_name = generate_random_file_name(exclude_extensions=exclude)
        file_path = SOURCE_DIRECTORY / "test" / file_name
        # Act
        dest_path = data_organizer.get_destination_path(SOURCE_DIRECTORY, file_path)
        # Assert
        assert dest_path == SOURCE_DIRECTORY / "other" / file_path.name


def test_get_all_files_without_subdirectories(tmp_path) -> None:
    """Tests all files are found (no sub-directories)."""
    # Arrange
    count = random.randint(0, 100)
    # Set comprehension here - even if the same file name is generated
    # multiple times (extremely unlikely), it will only count once.
    sample_files = {generate_random_file_name() for _ in range(count)}
    data_organizer = DataOrganizer(config_path=None)

    for file in sample_files:
        (tmp_path / file).write_text("")
    # Act
    all_files = data_organizer.get_all_files(tmp_path)
    # Assert
    assert len(all_files) == len(sample_files)


def test_get_all_files_with_subdirectories(tmp_path: Path) -> None:
    """Tests all files are found (including sub-directories)."""
    file_count = 0
    # Random number of sub-directories.
    sub_dir_count = random.randint(1, 10)
    for i in range(sub_dir_count):
        (tmp_path / f"subdir{i}").mkdir()
        # Random number of files in the sub-directory.
        sub_dir_file_count = random.randint(0, 10)
        # Again, set comprehension to avoid the risk of duplicate files.
        sample_files = {generate_random_file_name() for _ in range(sub_dir_file_count)}
        for file_name in sample_files:
            (tmp_path / f"subdir{i}" / file_name).write_text(" ")
        file_count += len(sample_files)

    data_organizer = DataOrganizer(config_path=None)

    # Act
    all_files = data_organizer.get_all_files(tmp_path)
    # Assert
    assert len(all_files) == file_count


def test_remove_empty_subdirectories(tmp_path: Path) -> None:
    """Tests that empty subdirectories are removed as expected."""
    sub_dir_count = random.randint(1, 100)
    for i in range(sub_dir_count):
        (tmp_path / f"subdir{i}").mkdir()
        if random.randint(0, 1):
            # 1 = True.
            # 50% chance of leaving the sub-directory empty, ready
            # to be removed.
            sub_dir_count -= 1
        else:
            # 0 = False.
            # 50% chance of adding a file to the sub-directory,
            # preventing it from being removed.
            file_name = generate_random_file_name()
            (tmp_path / f"subdir{i}" / file_name).write_text("")

    data_organizer = DataOrganizer(config_path=None)
    # Act
    data_organizer.remove_empty_subdirectories(tmp_path)
    # Assert
    assert len(tuple(tmp_path.iterdir())) == sub_dir_count
