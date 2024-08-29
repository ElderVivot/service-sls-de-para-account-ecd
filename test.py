from src.process_get_saldo_only_i155 import ProcessGetSaldoOnlyI155
from src.process_get_saldo_when_already_read_i155 import ProcessGetSaldoWhenAlreadyReadI155
from src.process_generate_lancs_with_depara import ProcessGenerateLancsWithDePara

idEcd = 'a4fa9ffa-97bd-462b-b279-7937ce3bd6db'
url = 'https://ecd-de-para-account-plan.s3.us-east-2.amazonaws.com/c86f99be-623f-4/eee08cc1-95dd-4258-a726-46f80b47fa4c.txt'

with open(f'data/t2.txt', 'r', encoding='cp1252', errors='ignore') as f:
    ProcessGenerateLancsWithDePara(f, idEcd=idEcd, url=url, folderTmp='tmp').executeJobMainAsync()
    # ProcessGetSaldoWhenAlreadyReadI155(f, idEcd=idEcd, url=url).executeJobMainAsync()
    # ProcessGetSaldoOnlyI155(f, idEcd=idEcd, url=url).executeJobMainAsync()
