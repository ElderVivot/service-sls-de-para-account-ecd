from src.process_get_saldo_only_i155 import ProcessGetSaldoOnlyI155
from src.process_get_saldo_when_already_read_i155 import ProcessGetSaldoWhenAlreadyReadI155
from src.process_generate_lancs_with_depara import ProcessGenerateLancsWithDePara

idEcd = 'bcc441fb-3b2b-4b87-a2c3-6be40a035408'
url = 'https://ecd-de-para-account-plan.s3.us-east-2.amazonaws.com/42d48d08-2dfa-4/bcc441fb-3b2b-4b87-a2c3-6be40a035408.txt'
testFile = 'data/t3.txt'

with open(testFile, 'r', encoding='cp1252', errors='ignore') as f:
    ProcessGenerateLancsWithDePara(f, idEcd=idEcd, url=url, folderTmp='tmp').executeJobMainAsync()
    # ProcessGetSaldoWhenAlreadyReadI155(f, idEcd=idEcd, url=url).executeJobMainAsync()
    # ProcessGetSaldoOnlyI155(f, idEcd=idEcd, url=url).executeJobMainAsync()
