"""The key functionality of the file organizer is based in this module."""
import json
import logging
import shutil
from pathlib import Path
from typing import Any, Callable, Optional


# Get the logger instance from the entrypoint file.
logger = logging.getLogger(__name__)


def handle_error(errors: Exception | tuple[Exception], message_format: str) -> Callable:
    """
    This utility decorator allows a function/method to have
    error handling implemented by inputting the errors(s) to
    catch, and the log message format if an error is caught.
    """

    def decorator(method: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            try:
                # Do whatever as usual.
                return method(*args, **kwargs)
            except errors as e:
                # In case an error occurs, log as required and raise.
                logger.error(message_format.format(e))
                raise e

        return wrapper

    return decorator


class DataOrganizer:
    """
    Class to organize data and files by managing the configuration
    and allowing a source directory to be input and processed.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        config = self._load_config(config_path) if config_path else {}
        # From the configuration (empty as required if not configured).
        self.directories = config.get("directories", {})
        self.file_types = config.get("file_types", {})
        self.ignore_list = config.get("ignore_list", [])

    @handle_error((OSError, json.JSONDecodeError), "Error loading config: {}")
    def _load_config(self, config_path: str) -> dict:
        """Loads the JSON configuration file as specified."""
        with open(config_path, "r") as f:
            return json.load(f)

    @handle_error((OSError, shutil.Error), "Error organizing files: {}")
    def organize_files(self, source_directory: str) -> None:
        """Performs the file organization as required."""
        # Converts the input string into a pathlib.Path object, which is
        # way easier and cleaner to handle than a string file path.
        source_directory = Path(source_directory)     
        for file_path in self.get_all_files(source_directory):
            if file_path.name in self.ignore_list:
                # File is in the ignored list - move on.
                continue
            # Identifies the destination file path based on the file's name.
            dest_path = self.get_destination_path(source_directory, file_path)
            # Moves the file as required.
            self.move_file(file_path, dest_path)
        # Delete any unused sub-directories after processing.
        self.remove_empty_subdirectories(source_directory)

    @handle_error(OSError, "Error getting all files: {}")
    def get_all_files(self, source_directory: Path) -> list[Path]:
        """
        Retrieves ALL files from a given source directory, recursively.
        This includes files in sub-folders, sub-sub-folders, etc.
        """
        return [path for path in source_directory.rglob("*") if path.is_file()]

    @handle_error(Exception, "Error getting destination path: {}")
    def get_destination_path(self, source_directory: Path, file_path: Path) -> Path:
        """Identifies the resulting file path for a given file."""
        # Parses the file extension without the period (.)

        extension = file_path.suffix.removeprefix(".").lower()

        # Finds either a file type name based on the available file types
        # and the corresponding extensions, defaulting to 'other'
        # if the extension does not belong in any of the categories.
        file_type = next(
            (
                file_type
                for file_type, extensions in self.file_types.items()
                if extension in extensions
            ),
            "other",
        )
        # Identifies the resulting directory based on the file type.
        dest_directory = source_directory / self.directories.get(file_type, "other")
        return dest_directory / file_path.name

    @handle_error((OSError, shutil.Error), "Error moving file: {}")
    def move_file(self, src_path: Path, dest_path: Path) -> None:
        """
        Moves a given path to another path,
        ensuring the new file path has the required folders created.
        """
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(src_path, dest_path)

    @handle_error(OSError, "Error removing empty subdirectories: {}")
    def remove_empty_subdirectories(self, directory: Path) -> None:
        """Deletes sub-directories with no files/folders inside.
        Identifies ALL sub-directories, including sub-sub-directories.
        SORTED IN REVERSE, to start with subdirectories of directories
        which if empty are removed, so the parent directory may also
        become empty can can be removed.
        E.g. "/path/a/b" > "/path/a" """
        subdirectories = sorted(
            (path for path in directory.rglob("*") if path.is_dir()), reverse=True
        )
        for subdirectory in subdirectories:
            if any(subdirectory.iterdir()):
                # At least one file/folder in the sub-directory, skipping.
                continue
            subdirectory.rmdir()
