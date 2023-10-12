
        provider "aws" {
          region = "us-west-1"
        }

        resource "aws_s3_bucket" "b" {
          bucket = "mybucket"
          acl    = "private"

          
        versioning {
          enabled = true
        }
        
          
        logging {
          target_bucket = "my-log-bucket"
          target_prefix = "log/"
        }
        
          
        server_side_encryption_configuration {
          rule {
            apply_server_side_encryption_by_default {
              sse_algorithm = "AES256"
            }
          }
        }
        
        }
        