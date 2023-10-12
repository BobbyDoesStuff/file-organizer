from dotenv import load_dotenv
import os
import subprocess

class TerraformGenerator:
    def __init__(self):
        # Load environment variables
        load_dotenv()

        # Extract details from .env
        self.access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.bucket_name = os.getenv("BUCKET_NAME", "default_bucket_name")
        self.region = os.getenv("AWS_REGION", "us-west-1")
        self.versioning = os.getenv("BUCKET_VERSIONING", "false").lower() == "true"
        self.logging = os.getenv("BUCKET_LOGGING", "false").lower() == "true"
        self.encryption = os.getenv("BUCKET_ENCRYPTION", "false").lower() == "true"

    def set_aws_credentials(self):
        os.environ["AWS_ACCESS_KEY_ID"] = self.access_key
        os.environ["AWS_SECRET_ACCESS_KEY"] = self.secret_key

    def generate_terraform_script(self):
        # Add configurations based on .env settings
        versioning_config = """
        versioning {
          enabled = true
        }
        """ if self.versioning else ""

        logging_config = """
        logging {
          target_bucket = "my-log-bucket"
          target_prefix = "log/"
        }
        """ if self.logging else ""

        encryption_config = """
        server_side_encryption_configuration {
          rule {
            apply_server_side_encryption_by_default {
              sse_algorithm = "AES256"
            }
          }
        }
        """ if self.encryption else ""

        # Create the Terraform script content
        tf_content = f"""
        provider "aws" {{
          region = "{self.region}"
        }}

        resource "aws_s3_bucket" "b" {{
          bucket = "{self.bucket_name}"
          acl    = "private"

          {versioning_config}
          {logging_config}
          {encryption_config}
        }}
        """

        # Save the script to a file
        with open("create_bucket.tf", "w") as f:
            f.write(tf_content)

    #def apply_terraform(self):
    #    self.set_aws_credentials()
    #    subprocess.run(["terraform", "init"], check=True)
    #    subprocess.run(["terraform", "apply", "-auto-approve"], check=True)

tf_generator = TerraformGenerator()
tf_generator.generate_terraform_script()
