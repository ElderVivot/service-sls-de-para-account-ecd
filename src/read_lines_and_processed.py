try:
    import unzip_requirements
except ImportError:
    pass

try:
    import io
    import os
    import asyncio
    import datetime
    from aiohttp import ClientSession
    from typing import Dict, Any, List
    import json
    from src.functions import removeCharSpecials, treatDecimalField, treatDateField
except Exception as e:
    print(f"Error importing libraries {e}")

API_HOST_SERVERLESS = os.environ.get('API_HOST_SERVERLESS')
API_HOST_DB_RELATIONAL = os.environ.get('API_HOST_DB_RELATIONAL')


class ReadLinesAndProcessed(object):
    def __init__(self) -> None:
        self.__dataToSave: Dict[str, Any] = {}
        self.__dataToSave['accountsDePara'] = []
        self.__accountsNameToCorrelation: Dict[str, str] = {}
        self.__accountsTypeToCorrelation: Dict[str, str] = {}

    async def __put(self, session: ClientSession, url: str, data: Any, headers: Dict[str, str]):
        async with session.put(url, json=data, headers=headers) as response:
            data = await response.json()
            return data, response.status

    async def __post(self, session: ClientSession, url: str, data: Any, headers: Dict[str, str]):
        async with session.post(url, json=data, headers=headers) as response:
            data = await response.json()
            return data, response.status

    async def __saveData(self, ):
        try:
            async with ClientSession() as session:
                response, statusCode = await self.__put(
                    session,
                    f"{API_HOST_SERVERLESS}/de-para-account-ecd",
                    data=json.loads(json.dumps(self.__dataToSave)),
                    headers={}
                )
                if statusCode >= 400:
                    raise Exception(statusCode, response)
                print('Salvo no banco de dados')

                await self.__saveDataApiRelational()

                return response
        except Exception as e:
            print('Error ao salvar dado dynamodb')
            print(e)

    async def __saveDataApiRelational(self):
        try:
            urlS3 = f"https://autmais-ecd-de-para-accounting-plan.s3.us-east-2.amazonaws.com/{self.__dataToSave['url']}"
            async with ClientSession() as session:

                response, statusCode = await self.__post(
                    session,
                    f"{API_HOST_DB_RELATIONAL}/de_para_ecd_account_plan",
                    data={
                        "nameCompanie": self.__dataToSave['nameCompanie'],
                        "federalRegistration": self.__dataToSave['federalRegistration'],
                        "startPeriod": self.__dataToSave['startPeriod'],
                        "endPeriod": self.__dataToSave['endPeriod'],
                        "urlFile": urlS3,
                        "typeLog": "success",
                        "messageLog": "SUCCESS",
                        "messageLogToShowUser": "Sucesso ao processar",
                        "messageError": ""
                    },
                    headers={"TENANT": self.__dataToSave['tenant']}
                )
                if statusCode >= 400:
                    raise Exception(statusCode, response)
                print('Salvo no banco de dados relacional')

                return response
        except Exception as e:
            print('Error ao salvar dado banco relacional')
            print(e)

    def __getTenant(self, key: str):
        try:
            return key.split('/')[0]
        except Exception:
            return ''

    def __getId(self, key: str):
        try:
            return key.split('/')[1].replace('.txt', '')
        except Exception:
            return key

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

    def __getTypeAccount(self, lineSplit: List[str]):
        try:
            return self.__accountsTypeToCorrelation[f'{lineSplit[2]}']
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
        balanceAccount = treatDecimalField(lineSplit[8])
        typeAccount = self.__getTypeAccount(lineSplit)
        oldAccount = str(lineSplit[2])

        if len(oldAccount) > 6:
            self.__dataToSave['codeOrClassification'] = 'classification'

        if balanceAccount > 0 and typeAccount == 'A':
            self.__dataToSave['accountsDePara'].append({
                "oldAccount": oldAccount,
                "newAccount": "",
                "nameAccount": self.__getNameAccount(lineSplit),
                "balanceAccount": treatDecimalField(lineSplit[8]),
                "kindBalanceAccount": lineSplit[9]
            })

    async def __readLinesAndProcessed(self, f: io.TextIOWrapper, key: str):
        lastI150File = False
        isFileECD = False

        self.__dataToSave['url'] = key
        self.__dataToSave['id'] = self.__getId(key)
        self.__dataToSave['tenant'] = self.__getTenant(key)
        dateTimeNow = datetime.datetime.now()
        miliSecondsThreeChars = dateTimeNow.strftime('%f')[0:3]
        self.__dataToSave['updatedAt'] = f"{dateTimeNow.strftime('%Y-%m-%dT%H:%M:%S')}.{miliSecondsThreeChars}Z"
        self.__dataToSave['codeOrClassification'] = 'code'

        while line := f.readline():
            try:
                lineFormated = removeCharSpecials(line)
                lineSplit = lineFormated.split('|')

                if isFileECD is False:
                    isFileECD = self.__checkIfIsFileECD(lineSplit)
                    if isFileECD is False:
                        print('Arquivo não é ECD')
                        self.__getDataFromIdentificador0000(lineSplit)
                        await self.__saveDataApiRelational()
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
                elif identificador == 'I200':
                    print('Terminou de processar todos registros do TXT')
                    break
                elif identificador == '9999':
                    print('Arquivo sem reg de I200, processou completo TXT')
                    break
                else:
                    continue
            except Exception as e:
                print('Error ao processar arquivo TXT')
                print(e)

        await self.__saveData()

    def executeJobMainAsync(self, f: io.TextIOWrapper, key: str):
        try:
            asyncio.run(self.__readLinesAndProcessed(f, key))
        except Exception:
            pass
