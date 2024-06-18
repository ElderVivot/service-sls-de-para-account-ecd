import json
from src.functions import removeCharSpecials

with open('data/_dataToSave.json') as f:
    dataJson = json.load(f)

    accountsDePara = dataJson['accountsDePara']

    with open('data/_dataToSave.txt', 'w') as fw:
        fw.write('Inicio|\n')
        fw.write('CtaNova|1000\n')

        balanceAccountTotal = 0
        for account in accountsDePara:
            oldAccount = account['oldAccount']
            oldAccountClassification = ''
            if len(oldAccount) > 6:
                oldAccountClassification = oldAccount
                oldAccount = ''
            nameAccount = removeCharSpecials(account['nameAccount']).upper()
            balanceAccount = account['balanceAccount']
            balanceAccountStr = f'{balanceAccount:.2f}'.replace('.', ',')
            kindBalanceAccount = account['kindBalanceAccount']
            fw.write(f'CtaAnt|{nameAccount}|{oldAccountClassification}|{balanceAccountStr}|{kindBalanceAccount}|\n')
            if kindBalanceAccount != 'D':
                print(account)
            else:
                balanceAccountTotal += balanceAccount
        print(balanceAccountTotal)
