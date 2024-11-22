try:
    import unzip_requirements
except ImportError:
    pass

try:
    import io
    import asyncio
    from src.process_without_de_para.generate_account_plan import GenerateAccountPlanWithoutDePara
    from src.process_without_de_para.generate_lancs import GenerateLancsWithoutDePara
except Exception as e:
    print(f"Error importing libraries {e}")


class ProcessWithoutDePara(object):
    def __init__(self, dataFile: io.TextIOWrapper, url='', tenant='', idEcd='', folderTmp='') -> None:
        self.__dataFile = dataFile
        self.__url = url
        self.__tenant = tenant
        self.__id = idEcd
        self.__idServerless = url.split('/')[-1].split('.')[0]
        self.__folderTmp = folderTmp

    async def __readLinesAndProcessed(self):
        accountPlanResult = GenerateAccountPlanWithoutDePara(self.__dataFile).process()
        accounts = accountPlanResult[0]
        tipoConta = accountPlanResult[1]
        await GenerateLancsWithoutDePara(self.__dataFile, self.__url, self.__tenant, self.__id, self.__folderTmp, accounts, tipoConta).readLinesAndProcessed()

    def executeJobMainAsync(self):
        try:
            asyncio.run(self.__readLinesAndProcessed())
        except Exception:
            pass
