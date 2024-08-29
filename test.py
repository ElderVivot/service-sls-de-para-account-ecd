from src.process_get_saldo_only_i155 import ProcessGetSaldoOnlyI155
from src.process_get_saldo_when_already_read_i155 import ProcessGetSaldoWhenAlreadyReadI155
from src.process_generate_lancs_with_depara import ProcessGenerateLancsWithDePara

with open(f'data/t2.txt', 'r', encoding='cp1252', errors='ignore') as f:
    ProcessGenerateLancsWithDePara(f, idEcd='72342ef2-955a-4f1f-8d66-af2dec726383', folderTmp='tmp',
                                   url='https://ecd-de-para-account-plan.s3.us-east-2.amazonaws.com/42d48d08-2dfa-4/72342ef2-955a-4f1f-8d66-af2dec726383.txt').executeJobMainAsync()
