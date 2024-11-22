try:
    import unzip_requirements
except ImportError:
    pass

try:
    import io
    import os
    import asyncio
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    from uuid import uuid4
    from typing import Dict, Any, List
    from src.functions import removeCharSpecials, treatDateFieldAsDate, treatDateField, returnDataInDictOrArray, \
        formatDate, treatTextField, treatDecimalField
    from src.save_data import SaveData
    from src.zip_files import ZipDataFiles
    from src.upload_to_cloudfare_r2 import AwsS3
except Exception as e:
    print(f"Error importing libraries {e}")

API_HOST_SERVERLESS = os.environ.get('API_HOST_SERVERLESS')
API_HOST_DB_RELATIONAL = os.environ.get('API_HOST_DB_RELATIONAL')


class GenerateLancsWithoutDePara(object):
    def __init__(self, dataFile: io.TextIOWrapper, url='', tenant='', idEcd='', folderTmp='', accounts=[], tipoConta=2) -> None:
        self.__dataFile = dataFile
        self.__url = url
        self.__tenant = tenant
        self.__id = idEcd
        self.__idServerless = url.split('/')[-1].split('.')[0]
        self.__accounts = accounts
        self.__tipoConta = tipoConta

        self.__accountsToDePara = {}
        self.__historicCode = {}

        self.__dataToSave: Dict[str, Any] = {}

        self.__limitLancsByFile = 10000
        self.__filesToZip = []
        self.__folderTmp = '/tmp' if folderTmp == '' else folderTmp

    def __getDePara(self):
        dataFileToWriteComPlanoReferencial = ''
        dataFileToWriteSemPlanoReferencial = ''
        try:
            for account in self.__accounts:
                try:
                    codeAccount = int(account[0])
                    classificationAccount = account[1]
                    nameAccount = treatTextField(account[2])
                    typeAccount = account[3]
                    dateAccount = f"{account[4][0:2]}/{account[4][2:4]}/{account[4][4:]}"
                    accountReferencial = "" if account[5] is None else account[5]

                    if self.__tipoConta == 1:
                        self.__accountsToDePara[f"{codeAccount}"] = int(codeAccount)
                    else:
                        self.__accountsToDePara[f"{classificationAccount}"] = int(codeAccount)

                    dataFileToWriteComPlanoReferencial += f"{codeAccount}|{classificationAccount}|{nameAccount}|{typeAccount}|{accountReferencial}\n"
                    dataFileToWriteSemPlanoReferencial += f"0200|{codeAccount}|{classificationAccount}|{typeAccount}|{nameAccount}|{dateAccount}|A||||||\n"
                except Exception:
                    pass

            pathToSave = f'{self.__folderTmp}/contas_COM_plano_referencial.txt'
            self.__filesToZip.append(pathToSave)
            with open(pathToSave, 'w') as fWrite:
                fWrite.write(dataFileToWriteComPlanoReferencial)

            pathToSave = f'{self.__folderTmp}/contas_SEM_plano_referencial.txt'
            self.__filesToZip.append(pathToSave)
            with open(pathToSave, 'w') as fWrite:
                fWrite.write(dataFileToWriteSemPlanoReferencial)

        except Exception as e:
            print('ERROR', e)

    def __checkIfIsFileECD(self, lineSplit: List[str]):
        if len(lineSplit) < 2:
            return False
        if lineSplit[1] == '0000':
            field02 = lineSplit[2].upper()
            if field02 != 'LECD':
                return False
        return True

    def __getDataFromIdentificador0000(self, lineSplit: List[str]):
        try:
            self.__dataToSave['startPeriod'] = treatDateField(lineSplit[3], 4)
            self.__dataToSave['endPeriod'] = treatDateField(lineSplit[4], 4)
            self.__dataToSave['nameCompanie'] = lineSplit[5]
            self.__dataToSave['federalRegistration'] = lineSplit[6]
        except Exception:
            pass

    def __getDataFromIdentificadorI075(self, lineSplit: List[str]) -> str:
        codeHistoric = lineSplit[2]
        descriptionHistoric = lineSplit[3]
        self.__historicCode[f'{codeHistoric}'] = descriptionHistoric

    def __getDataFromIdentificadorI200(self, lineSplit: List[str]) -> str:
        dateMovement = lineSplit[3]
        dateMovement = treatDateField(dateMovement, 4)
        dateMovement = f'{dateMovement[8:10]}/{dateMovement[5:7]}/{dateMovement[0:4]}'

        return dateMovement

    def __getDataFromIdentificadorI155(self, lineSplit: List[str], dateLanc: str):
        balanceAccount = lineSplit[4]
        balanceAccountDecimal = treatDecimalField(balanceAccount)
        oldAccount = str(lineSplit[2])
        newAccount = returnDataInDictOrArray(self.__accountsToDePara, [oldAccount], '')
        kindBalanceAccount = lineSplit[5]

        if balanceAccountDecimal > 0:
            if kindBalanceAccount == 'D':
                return f"6100|{dateLanc}|{newAccount}||{balanceAccount}||SALDO DA ECD EM {dateLanc}||||\r\n"
            else:
                return f"6100|{dateLanc}||{newAccount}|{balanceAccount}||SALDO DA ECD EM {dateLanc}||||\r\n"

    def __getDataFromIdentificadorI250(self, lineSplit: List[str], dateMovement) -> str:
        oldAccount = str(lineSplit[2])
        newAccount = returnDataInDictOrArray(self.__accountsToDePara, [oldAccount])
        amountLanc = lineSplit[4]
        naturezaLanc = lineSplit[5]
        codeHistoric = str(lineSplit[7])
        descriptionCodeHistoric = returnDataInDictOrArray(self.__historicCode, [codeHistoric], '')
        historic = treatTextField(descriptionCodeHistoric + ' ' + lineSplit[8])
        accountDebit = newAccount if naturezaLanc == 'D' else ''
        accountCredit = newAccount if naturezaLanc == 'C' else ''

        newLine = f"6100|{dateMovement}|{accountDebit}|{accountCredit}|{amountLanc}||{historic}||||\n"
        return newLine

    def __uploadToR2(self):
        bufferSave = ZipDataFiles(self.__folderTmp).getZipBuffer()

        bucketName = 'autmais-generic'
        idR2 = str(uuid4())
        pathToSaveR2 = f"de-para-ecd-lancs/{self.__tenant}/{self.__dataToSave['federalRegistration']}_{idR2[0:15]}.zip"

        # try:
        #     AwsS3().delete(bucketName, pathToSaveR2)
        # except Exception as e:
        #     print(e)

        AwsS3().upload(bufferSave, pathToSaveR2, 'application/zip', bucketName)

        self.__dataToSave['urlFileReady'] = f"https://files-autmais-generic.autmais.com/{pathToSaveR2}"

    async def readLinesAndProcessed(self):
        try:
            isFileECD = False
            firstI150File = False
            dateMovement = None
            dateBalanceInitial = None
            countNumberFile = 1
            numberLancsFileActual = 0
            dataFileToWrite = ''
            dataFileToWriteBalanceInitial = ''
            numberLineI200 = 0
            dataFileToWriteI200 = ''

            self.__getDePara()

            self.__dataToSave['url'] = self.__url
            self.__dataToSave['id'] = self.__idServerless
            self.__dataToSave['idDeParaECDAccountPlan'] = self.__id
            self.__dataToSave['urlFileReady'] = ''
            self.__dataToSave['generateLancs'] = '1'
            self.__dataToSave['tenant'] = self.__tenant
            dateTimeNow = datetime.now()
            miliSecondsThreeChars = dateTimeNow.strftime('%f')[0:3]
            self.__dataToSave['updatedAt'] = f"{dateTimeNow.strftime('%Y-%m-%dT%H:%M:%S')}.{miliSecondsThreeChars}Z"
            self.__dataToSave['codeOrClassification'] = 'code'

            numberLine = 0
            self.__dataFile.seek(0)
            while line := self.__dataFile.readline():
                numberLine += 1
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
                        startPeriod = lineSplit[3]
                        self.__getDataFromIdentificador0000(lineSplit)
                        dataFileToWrite = f"0000|{self.__dataToSave['federalRegistration']}|\n"
                    elif identificador == 'I075':
                        self.__getDataFromIdentificadorI075(lineSplit)
                    elif identificador == 'I150':
                        competenceStartI150 = lineSplit[2]
                        if competenceStartI150 == startPeriod:
                            firstI150File = True
                            dateBalanceInitial = treatDateFieldAsDate(competenceStartI150, 4) - relativedelta(days=1)
                            dateBalanceInitial = formatDate(dateBalanceInitial, '%d/%m/%Y')
                            dataFileToWriteBalanceInitial = f"0000|{self.__dataToSave['federalRegistration']}|\n"
                            dataFileToWriteBalanceInitial += '6000|V||||\n'
                        else:
                            firstI150File = False
                    elif identificador == 'I155' and firstI150File is True:
                        resultI155 = self.__getDataFromIdentificadorI155(lineSplit, dateBalanceInitial)
                        if resultI155 is not None:
                            dataFileToWriteBalanceInitial += resultI155
                    elif identificador == 'I200':
                        dateMovement = self.__getDataFromIdentificadorI200(lineSplit)

                        if numberLancsFileActual > self.__limitLancsByFile:
                            pathToSave = f'{self.__folderTmp}/lancamentos_arquivo_{countNumberFile}.txt'
                            self.__filesToZip.append(pathToSave)
                            with open(pathToSave, 'w') as fWrite:
                                fWrite.write(dataFileToWrite)
                            dataFileToWrite = f"0000|{self.__dataToSave['federalRegistration']}|\n"
                            numberLancsFileActual = 0
                            countNumberFile += 1

                        if numberLineI200 <= 2 and numberLineI200 > 0:
                            dataFileToWrite += '6000|X||||\n'

                            dataFileToWriteI200Split = []
                            dataFileToWriteI200Split = dataFileToWriteI200.split('\n')

                            primeiraLinhaI250 = dataFileToWriteI200Split[0]
                            segundaLinhaI250 = dataFileToWriteI200Split[1]
                            contaDebito = primeiraLinhaI250.split('|')[2]
                            contaCredito = primeiraLinhaI250.split('|')[3]
                            if contaDebito == '':
                                contaDebito = segundaLinhaI250.split('|')[2]
                            if contaCredito == '':
                                contaCredito = segundaLinhaI250.split('|')[3]
                            primeiraLinhaI250Split = primeiraLinhaI250.split('|')
                            primeiraLinhaI250Split[2] = contaDebito
                            primeiraLinhaI250Split[3] = contaCredito

                            dataFileToWrite += '|'.join(primeiraLinhaI250Split) + '\n'
                        if numberLineI200 > 0 and numberLineI200 > 2:
                            dataFileToWrite += '6000|V||||\n'
                            dataFileToWrite += dataFileToWriteI200

                        numberLineI200 = 0
                        dataFileToWriteI200 = ''

                    elif identificador == 'I250':
                        dataFileToWriteI200 += self.__getDataFromIdentificadorI250(lineSplit, dateMovement)
                        # dataFileToWrite += self.__getDataFromIdentificadorI250(lineSplit, dateMovement)
                        numberLancsFileActual += 1
                        numberLineI200 += 1
                    elif identificador == '9999':
                        pathToSave = f'{self.__folderTmp}/lancamentos_arquivo_{countNumberFile}.txt'
                        self.__filesToZip.append(pathToSave)
                        with open(pathToSave, 'w') as fWrite:
                            fWrite.write(dataFileToWrite)

                        pathToSave = f'{self.__folderTmp}/saldo_inicial.txt'
                        self.__filesToZip.append(pathToSave)
                        with open(pathToSave, 'w') as fWrite:
                            fWrite.write(dataFileToWriteBalanceInitial)
                        print('Arquivo processado por completo')
                        break
                    else:
                        continue
                except Exception as e:
                    print('ERROR process_generate_lancs_with_de_para', numberLine, e)

            ZipDataFiles(self.__folderTmp).zip(self.__filesToZip)

            self.__dataToSave['typeLog'] = "success"
            self.__dataToSave["messageLog"] = "SUCCESS"
            self.__dataToSave["messageLogToShowUser"] = "Sucesso ao processar"
            self.__dataToSave["messageError"] = ''

            if self.__url != '' and self.__tenant != '':
                self.__uploadToR2()
                await SaveData(self.__dataToSave).saveDataApiRelational()
            else:
                import json
                import base64
                import sys
                import gzip

                # print('---', self.__folderTmp)
                ZipDataFiles(self.__folderTmp).getZipBuffer()

                dataBytes = bytes(json.dumps(self.__dataToSave), 'utf-8')
                dataEncoded = base64.b64encode(dataBytes)
                dataCompress = gzip.compress(dataBytes)
                print(f'-dataCompress={sys.getsizeof(dataCompress)}',
                      f'dataEncoded={sys.getsizeof(dataEncoded)}',
                      f'dataBytes={sys.getsizeof(dataBytes)}', sep='\n-')

                jsonData = json.dumps(self.__dataToSave, indent=4)
                # jsonData = json.dumps({"data": dataEncoded.decode()}, indent=4)
                # jsonData = json.dumps(dataCompress, indent=4)
                with open('data/_dataToSave.json', 'w') as outfile:
                    outfile.write(jsonData)
        except Exception as e:
            print('ERROR', e)
