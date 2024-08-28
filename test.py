from src.process_get_saldo_only_i155 import ProcessGetSaldoOnlyI155
from src.process_get_saldo_when_already_read_i155 import ProcessGetSaldoWhenAlreadyReadI155

with open(f'data/t2.txt', 'r', encoding='cp1252', errors='ignore') as f:
    ProcessGetSaldoWhenAlreadyReadI155(f, idEcd='72342ef2-955a-4f1f-8d66-af2dec726383').executeJobMainAsync()
