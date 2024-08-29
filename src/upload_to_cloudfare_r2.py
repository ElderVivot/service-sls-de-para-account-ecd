try:
    import unzip_requirements
except ImportError:
    pass

try:
    import os
    import boto3
    from botocore.exceptions import ClientError
    from dotenv import load_dotenv
except Exception as e:
    print(f"Error importing libraries {e}")

# Load environment variables
load_dotenv()

# Configuration for AWS S3
config_aws = {
    'endpoint_url': os.getenv('CLOUDFARE_R2_ENDPOINT'),
    'aws_access_key_id': os.getenv('CLOUDFARE_R2_ACCESS_KEY_ID'),
    'aws_secret_access_key': os.getenv('CLOUDFARE_R2_SECRET_ACCESS_KEY'),
    'region_name': os.getenv('CLOUDFARE_R2_REGION')
}


class AwsS3(object):
    def __init__(self):
        self.connection = boto3.client('s3', **config_aws)

    def upload(self, data_upload, key_to_save, content_type, s3_bucket_name):
        try:
            response = self.connection.put_object(
                Bucket=s3_bucket_name,
                Key=key_to_save,
                Body=data_upload,
                ContentType=content_type,
                ACL='public-read'
            )
            return response
        except ClientError as e:
            print(f"An error occurred: {e}")
            raise

    def delete(self, bucket, key):
        try:
            response = self.connection.delete_object(
                Bucket=bucket,
                Key=key
            )
            return response
        except ClientError as e:
            print(f"An error occurred: {e}")
