import boto3
import botocore.exceptions
import hashlib
from retry import retry
from dotenv import load_dotenv
import logging
from pathlib import Path
import os


class S3Uploader:
    def __init__(self, bucket_name: str):
        load_dotenv()
        session = boto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )
        self.s3 = session.client("s3")
        self.bucket_name = bucket_name

    def calculate_md5(self, filepath: Path) -> str:
        """Calculate and return the MD5 hash of a file."""
        hash_md5 = hashlib.md5()
        with filepath.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def get_s3_uploaded_object_md5sum(self, resource_name: str) -> str:
        """Retrieve the MD5 hash of an object in S3."""
        try:
            md5sum = self.s3.head_object(
                Bucket=self.bucket_name, Key=resource_name
            )["ETag"][1:-1]
        except botocore.exceptions.ClientError:
            md5sum = None
        return md5sum

    def all_files(self, root_directory: Path):
        """Generator to yield all file paths within the root directory."""
        for file in root_directory.rglob("*"):
            if file.is_file():
                yield file

    @retry(
        (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError),
        tries=3,
        delay=3,
        backoff=2,
    )
    def upload_directory(self, root_directory: Path) -> None:
        """Upload all files in the directory to S3, preserving the directory structure."""
        for file_path in self.all_files(root_directory):
            relative_path = file_path.relative_to(root_directory)
            self.upload_file(file_path, str(relative_path))

    def validate_object_lock(self) -> bool:
        """Verify if the S3 bucket's object lock matches the settings in the .env file."""
        try:
            lock_config = self.s3.get_bucket_object_lock_configuration(
                Bucket=self.bucket_name
            )

            # Extract the Object Lock settings from the .env file
            desired_mode = os.getenv("OBJECT_LOCK_DEFAULT_MODE")
            desired_days = int(os.getenv("OBJECT_LOCK_DEFAULT_DAYS"))

            # Extract settings from the current S3 bucket configuration
            current_mode = lock_config["ObjectLockConfiguration"]["Rule"][
                "DefaultRetention"
            ]["Mode"]
            current_days = int(
                lock_config["ObjectLockConfiguration"]["Rule"][
                    "DefaultRetention"
                ]["Days"]
            )

            if current_mode == desired_mode and current_days == desired_days:
                return True
            logger.critical(
                "Object Lock settings in the bucket do not match the desired configuration!"
            )
            return False

        except botocore.exceptions.ClientError as e:
            logger.error("Error retrieving Object Lock configuration: %s", e)
            return False

    def upload_file(self, filepath: Path, s3_key: str) -> bool:
        """Upload individual file to S3 and ensure its integrity by checking MD5 hashes."""
        # Calculate original file's MD5
        original_md5 = self.calculate_md5(filepath)

        # Upload file to S3 using the upload_file method
        self.s3.upload_file(
            Filename=str(filepath), Bucket=self.bucket_name, Key=s3_key
        )

        # Check uploaded file's MD5
        # If hashes don't match, it means file was uploaded corrupted
        uploaded_md5 = self.get_s3_uploaded_object_md5sum(s3_key)

        if original_md5 == uploaded_md5:
            logger.info("File %s uploaded successfully!", filepath.name)
            return True
        else:
            logger.warning(
                "File %s uploaded but MD5 hash doesn't match. Integrity might be compromised.",
                filepath.name,
            )

            # Delete the corrupted file from S3
            self.s3.delete_object(Bucket=self.bucket_name, Key=s3_key)

            # Raise an ClientError so the retry decorator can catch it and retry the operation
            raise botocore.exceptions.ClientError(
                f"File {filepath.name} upload failed due to MD5 hash mismatch."
            )


def setup_logging():
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)


if __name__ == "__main__":
    logger = setup_logging()

    BUCKET_NAME = "your-bucket-name"  # replace with your bucket name
    FILE_PATH = Path("path-to-your-file")  # replace with your file path

    uploader = S3Uploader(BUCKET_NAME)
    uploader.upload_directory(FILE_PATH)