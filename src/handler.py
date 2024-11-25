try:
    import unzip_requirements
except ImportError:
    pass

try:
    import boto3
    import os
    from smart_open import open
    from src.functions import returnDataInDictOrArray
    from src.process_get_saldo_only_i155 import ProcessGetSaldoOnlyI155
    from src.process_get_saldo_when_already_read_i155 import ProcessGetSaldoWhenAlreadyReadI155
    from src.process_generate_lancs_with_depara import ProcessGenerateLancsWithDePara
    from src.process_without_de_para.__main__ import ProcessWithoutDePara
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
        s3 = item.get("dynamodb")
        url = s3.get("NewImage").get("url").get("S")
        tenant = s3.get("NewImage").get("tenant").get("S")
        idEcd = s3.get("NewImage").get("id").get("S")
        typeToGenerate = returnDataInDictOrArray(s3, ['NewImage', 'typeToGenerate', 'S'], None)

        urlSplit = url.split('/')
        bucket = urlSplit[2].split('.')[0]
        key = '/'.join(urlSplit[3:])
        print(bucket, key, idEcd, typeToGenerate, sep=' | ')

        try:
            with open(f's3://{bucket}/{key}', 'r', encoding='cp1252', transport_params={"client": client}, errors='ignore') as f:
                if typeToGenerate == 'get_accounts_already_generate_by_saldo':
                    ProcessGetSaldoWhenAlreadyReadI155(f, url, tenant, idEcd).executeJobMainAsync()
                elif typeToGenerate == 'generate_lancs_with_de_para':
                    ProcessGenerateLancsWithDePara(f, url, tenant, idEcd).executeJobMainAsync()
                elif typeToGenerate == 'generate_lancs_without_de_para':
                    ProcessWithoutDePara(f, url, tenant, idEcd).executeJobMainAsync()
                else:
                    ProcessGetSaldoOnlyI155(f, url, tenant, idEcd).executeJobMainAsync()
        except Exception:
            with open(f's3://{bucket}/{key}', 'r', transport_params={"client": client}, errors='ignore') as f:
                if typeToGenerate == 'get_accounts_already_generate_by_saldo':
                    ProcessGetSaldoWhenAlreadyReadI155(f, url, tenant, idEcd).executeJobMainAsync()
                elif typeToGenerate == 'generate_lancs_with_de_para':
                    ProcessGenerateLancsWithDePara(f, url, tenant, idEcd).executeJobMainAsync()
                elif typeToGenerate == 'generate_lancs_without_de_para':
                    ProcessWithoutDePara(f, url, tenant, idEcd).executeJobMainAsync()
                else:
                    ProcessGetSaldoOnlyI155(f, url, tenant, idEcd).executeJobMainAsync()
