try:
    import unzip_requirements
except ImportError:
    pass

try:
    import io
    import os
    import asyncio
    import datetime
    from typing import Dict, Any, List
    from src.functions import removeCharSpecials, treatDecimalField, treatDateField, returnDataInDictOrArray
    from src.save_data import SaveData
    from src.get_de_para import GetDePara
except Exception as e:
    print(f"Error importing libraries {e}")

API_HOST_SERVERLESS = os.environ.get('API_HOST_SERVERLESS')
API_HOST_DB_RELATIONAL = os.environ.get('API_HOST_DB_RELATIONAL')


class ProcessGetSaldoWhenAlreadyReadI155(object):
    def __init__(self, dataFile: io.TextIOWrapper, url='', tenant='', idEcd='') -> None:
        self.__dataFile = dataFile
        self.__url = url
        self.__tenant = tenant
        self.__id = idEcd
        self.__idServerless = url.split('/')[-1].split('.')[0]

        self.__deParaAlreadyExist = {}

        self.__dataToSave: Dict[str, Any] = {}
        self.__accountsNameToCorrelation: Dict[str, str] = {}
        self.__accountsTypeToCorrelation: Dict[str, str] = {}

        self.__accounts = {}

    async def __getDePara(self):
        try:
            getDePara = await GetDePara(self.__idServerless).get()
            self.__dataToSave = returnDataInDictOrArray(getDePara, ['Item'])
            accountsDePara = returnDataInDictOrArray(self.__dataToSave, ['accountsDePara'])
            for account in accountsDePara:
                try:
                    self.__deParaAlreadyExist[f"{account['oldAccount']}"] = account['newAccount']
                except Exception:
                    pass
        except Exception as e:
            print('ERROR', e)

    def __getDataFromIdentificador0000(self, lineSplit: List[str]):
        try:
            self.__dataToSave['startPeriod'] = treatDateField(lineSplit[3], 4)
            self.__dataToSave['endPeriod'] = treatDateField(lineSplit[4], 4)
            self.__dataToSave['nameCompanie'] = lineSplit[5]
            self.__dataToSave['federalRegistration'] = lineSplit[6]
        except Exception:
            pass

    def __getNameAccount(self, lineSplit: List[str]):
        try:
            return self.__accountsNameToCorrelation[f'{lineSplit[2]}']
        except Exception:
            return ''

    def __checkIfIsFileECD(self, lineSplit: List[str]):
        if len(lineSplit) < 2:
            return False
        if lineSplit[1] == '0000':
            field02 = lineSplit[2].upper()
            if field02 != 'LECD':
                return False
        return True

    def __getDataFromIdentificadorI155(self, lineSplit: List[str]):
        oldAccount = str(lineSplit[2])

        if len(oldAccount) > 6:
            self.__dataToSave['codeOrClassification'] = 'classification'

        self.__accounts[f'{oldAccount}'] = {
            "oldAccount": oldAccount,
            "newAccount": "",
            "nameAccount": self.__getNameAccount(lineSplit),
            "balanceAccount": treatDecimalField(lineSplit[8]),
            "kindBalanceAccount": lineSplit[9],
            "existLancs": False
        }

    def __getDataFromIdentificadorI250(self, lineSplit: List[str]):
        oldAccount = str(lineSplit[2])

        if len(oldAccount) > 6:
            self.__dataToSave['codeOrClassification'] = 'classification'

        self.__accounts[f'{oldAccount}']['existLancs'] = True

    def __correlationAccounts(self):
        self.__dataToSave['accountsDePara'] = []
        for oldAccount, account in self.__accounts.items():
            try:
                existLancs = returnDataInDictOrArray(account, ['existLancs'])
                newAccountAlreadyIdentifie = returnDataInDictOrArray(self.__deParaAlreadyExist, [oldAccount], None)
                if existLancs is True or newAccountAlreadyIdentifie is not None:
                    self.__dataToSave['accountsDePara'].append({
                        "oldAccount": oldAccount,
                        "newAccount": newAccountAlreadyIdentifie if newAccountAlreadyIdentifie is not None else '',
                        "nameAccount": account['nameAccount'],
                        "balanceAccount": account['balanceAccount'],
                        "kindBalanceAccount": account['kindBalanceAccount']
                    })
            except Exception:
                pass

    async def __readLinesAndProcessed(self):
        try:
            lastI150File = False
            isFileECD = False

            await self.__getDePara()

            self.__dataToSave['url'] = self.__url
            self.__dataToSave['id'] = self.__idServerless
            self.__dataToSave['idDeParaECDAccountPlan'] = self.__id
            self.__dataToSave['tenant'] = self.__tenant
            dateTimeNow = datetime.datetime.now()
            miliSecondsThreeChars = dateTimeNow.strftime('%f')[0:3]
            self.__dataToSave['updatedAt'] = f"{dateTimeNow.strftime('%Y-%m-%dT%H:%M:%S')}.{miliSecondsThreeChars}Z"
            self.__dataToSave['codeOrClassification'] = 'code'

            while line := self.__dataFile.readline():
                try:
                    lineFormated = removeCharSpecials(line)
                    lineSplit = lineFormated.split('|')

                    if isFileECD is False:
                        isFileECD = self.__checkIfIsFileECD(lineSplit)
                        if isFileECD is False:
                            print('Arquivo não é ECD')
                            self.__getDataFromIdentificador0000(lineSplit)
                            await SaveData(self.__dataToSave).saveDataApiRelational()
                            break

                    identificador = lineSplit[1]

                    if identificador == '0000':
                        endPeriod = lineSplit[4]
                        self.__getDataFromIdentificador0000(lineSplit)
                    elif identificador == 'I050':
                        self.__accountsNameToCorrelation[f'{lineSplit[6]}'] = lineSplit[8]
                        self.__accountsTypeToCorrelation[f'{lineSplit[6]}'] = lineSplit[4]
                    elif identificador == 'I150':
                        competenceEndI150 = lineSplit[3]
                        if competenceEndI150 == endPeriod:
                            lastI150File = True
                        else:
                            continue
                    elif identificador == 'I155' and lastI150File is True:
                        self.__getDataFromIdentificadorI155(lineSplit)
                    elif identificador == 'I250':
                        self.__getDataFromIdentificadorI250(lineSplit)
                    elif identificador == '9999':
                        print('Arquivo processado por completo')
                        break
                    else:
                        continue
                except Exception as e:
                    print('Error ao processar arquivo TXT')
                    print(e)

            self.__correlationAccounts()

            if self.__url != '' and self.__tenant != '':
                await SaveData(self.__dataToSave).saveData()
            else:
                import json
                import base64
                import sys
                import gzip

                dataBytes = bytes(json.dumps(self.__dataToSave), 'utf-8')
                dataEncoded = base64.b64encode(dataBytes)
                dataCompress = gzip.compress(dataBytes)
                print(f'-dataCompress={sys.getsizeof(dataCompress)}',
                      f'dataEncoded={sys.getsizeof(dataEncoded)}',
                      f'dataBytes={sys.getsizeof(dataBytes)}',
                      f"lenAccountsDePara={len(self.__dataToSave['accountsDePara'])}", sep='\n-')

                jsonData = json.dumps(self.__dataToSave, indent=4)
                # jsonData = json.dumps({"data": dataEncoded.decode()}, indent=4)
                # jsonData = json.dumps(dataCompress, indent=4)
                with open('data/_dataToSave.json', 'w') as outfile:
                    outfile.write(jsonData)
        except Exception as e:
            print('ERROR', e)

    def executeJobMainAsync(self):
        try:
            asyncio.run(self.__readLinesAndProcessed())
        except Exception:
            pass
