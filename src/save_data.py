try:
    import unzip_requirements
except ImportError:
    pass

try:
    import uuid
    import os
    import gzip
    import base64
    from aiohttp import ClientSession
    from typing import Dict, Any, List
    import json
except Exception as e:
    print(f"Error importing libraries {e}")

API_HOST_SERVERLESS = os.environ.get('API_HOST_SERVERLESS')
API_HOST_DB_RELATIONAL = os.environ.get('API_HOST_DB_RELATIONAL')


class SaveData(object):
    def __init__(self, dataToSave: Dict[str, Any]) -> None:
        self.__dataToSave = dataToSave

    async def __put(self, session: ClientSession, url: str, data: Any, headers: Dict[str, str]):
        async with session.put(url, json=data, headers=headers) as response:
            data = await response.json()
            return data, response.status

    # IMPLEMENTING TO SAVE DATA SPLIT ACCOUNT DE PARA BECAUSE LIMIT OF DYNAMODB
    # async def saveData(self, ):
    #     try:
    #         lenghtData = len(self.__dataToSave['accountsDePara'])
    #         accountsDeParaOriginal = self.__dataToSave['accountsDePara']
    #         qtdTimesSplit = int(lenghtData / 10000) + 1
    #         loopProcessing = 0
    #         messageLogOriginal = self.__dataToSave['messageLogToShowUser']
    #         urlFile = self.__dataToSave['url'].split('/')[-1]

    #         async with ClientSession() as session:
    #             for idx in range(0, lenghtData, 10000):
    #                 loopProcessing += 1
    #                 if idx > 0:
    #                     self.__dataToSave['id'] = str(uuid.uuid4())
    #                     self.__dataToSave['accountsDePara'] = accountsDeParaOriginal[idx: idx + 10000]
    #                 else:
    #                     self.__dataToSave['accountsDePara'] = accountsDeParaOriginal[0: idx + 10000]
    #                 dataJson = json.dumps(self.__dataToSave)
    #                 dataBytes = bytes(dataJson, 'utf-8')
    #                 dataCompress = gzip.compress(dataBytes)
    #                 dataEncoded = base64.b64encode(dataCompress)

    #                 response, statusCode = await self.__put(
    #                     session,
    #                     f"{API_HOST_SERVERLESS}/de-para-account-ecd-zip",
    #                     data=json.loads(json.dumps({"data": dataEncoded.decode()})),
    #                     headers={}
    #                 )
    #                 if statusCode >= 400:
    #                     raise Exception(statusCode, response)
    #                 print('Salvo no banco de dados')

    #                 if qtdTimesSplit > 1:
    #                     self.__dataToSave['messageLogToShowUser'] = f"{messageLogOriginal}. Parte {loopProcessing} de {qtdTimesSplit} do arquivo {urlFile[0:7]}"

    #                 if idx > 0:
    #                     await self.saveDataApiRelational()
    #                 else:
    #                     result = await self.saveDataApiRelational()
    #                     self.__dataToSave["idUser"] = result['idUser']
    #                     self.__dataToSave["nameFinancial"] = result['nameFinancial']

    #             return response
    #     except Exception as e:
    #         print('Error ao salvar dado dynamodb')
    #         print(e)
    #         self.__dataToSave['typeLog'] = 'error'
    #         self.__dataToSave['messageLog'] = str(e)
    #         self.__dataToSave['messageLogToShowUser'] = 'Erro ao salvar resultado do processamento'

    #         await self.saveDataApiRelational()

    async def saveData(self, ):
        try:
            dataJson = json.dumps(self.__dataToSave)
            dataBytes = bytes(dataJson, 'utf-8')
            dataCompress = gzip.compress(dataBytes)
            dataEncoded = base64.b64encode(dataCompress)

            async with ClientSession() as session:
                response, statusCode = await self.__put(
                    session,
                    f"{API_HOST_SERVERLESS}/de-para-account-ecd-zip",
                    data=json.loads(json.dumps({"data": dataEncoded.decode()})),
                    headers={}
                )
                if statusCode >= 400:
                    self.__dataToSave['typeLog'] = 'error'
                    self.__dataToSave['messageLog'] = 'ERROR_SAVE_DATA_DYNAMO'
                    self.__dataToSave['messageLogToShowUser'] = 'Erro ao salvar resultado do relacionamento, entre em contato com suporte.'
                    self.__dataToSave['messageError'] = f"{statusCode} - {str(response)}"
                    await self.saveDataApiRelational()
                    raise Exception(statusCode, response)
                print('Salvo no banco de dados')

                await self.saveDataApiRelational()

                return response
        except Exception as e:
            print('Error ao salvar dado dynamodb')
            print(e)

    async def saveDataApiRelational(self):
        try:
            async with ClientSession() as session:
                response, statusCode = await self.__put(
                    session,
                    f"{API_HOST_DB_RELATIONAL}/de_para_ecd_account_plan/{self.__dataToSave['idDeParaECDAccountPlan']}",
                    data={
                        "idDeParaECDAccountPlan": self.__dataToSave['idDeParaECDAccountPlan'],
                        "nameCompanie": self.__dataToSave['nameCompanie'],
                        "federalRegistration": self.__dataToSave['federalRegistration'],
                        "startPeriod": self.__dataToSave['startPeriod'],
                        "endPeriod": self.__dataToSave['endPeriod'],
                        "urlFile": self.__dataToSave['url'],
                        "typeLog": self.__dataToSave['typeLog'],
                        "messageLog": self.__dataToSave['messageLog'],
                        "messageLogToShowUser": self.__dataToSave['messageLogToShowUser'],
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
