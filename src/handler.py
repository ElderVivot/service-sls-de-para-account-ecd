try:
    import unzip_requirements
except ImportError:
    pass

try:
    import boto3
    import os
    from smart_open import open
    from src.read_lines_and_processed import ReadLinesAndProcessed
except Exception as e:
    print("Error importing libraries", e)


AWS_ACCESS_KEY_ID = os.environ.get('AWS_S3_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_S3_SECRET_ACCESS_KEY')
REGION_NAME = os.environ.get('AWS_S3_REGION')


def main(event, context):

    client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=REGION_NAME)

    for item in event.get("Records"):
        print(item)
        s3 = item.get("s3")
        bucket = s3.get("bucket").get("name")
        key = s3.get("object").get("key")

        try:
            with open(f's3://{bucket}/{key}', 'r', encoding='cp1252', transport_params={"client": client}) as f:
                ReadLinesAndProcessed().executeJobMainAsync(f, key)
        except Exception:
            with open(f's3://{bucket}/{key}', 'r', transport_params={"client": client}) as f:
                ReadLinesAndProcessed().executeJobMainAsync(f, key)
