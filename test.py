from src.process_saldo import ProcessSaldo
from src.process_lancs_when_already_process_saldo import ProcessLancsWhenAlreadyProcessSaldo

with open(f'data/t2.txt', 'r', encoding='cp1252', errors='ignore') as f:
    ProcessLancsWhenAlreadyProcessSaldo(f, idEcd='72342ef2-955a-4f1f-8d66-af2dec726383').executeJobMainAsync()
