try:
    import unzip_requirements
except ImportError:
    pass

try:
    import os
    from aiohttp import ClientSession
    from dotenv import load_dotenv
    from src.requests_adapter import get
except Exception as e:
    print(f"Error importing libraries {e}")

load_dotenv()


API_HOST_SERVERLESS = os.environ.get('API_HOST_SERVERLESS')


class GetDePara(object):
    def __init__(self, idEcd: str) -> None:
        self.__id = idEcd

    async def get(self):
        try:
            url = f"{API_HOST_SERVERLESS}/de-para-account-ecd/{self.__id}"
            async with ClientSession() as session:
                response, statusCode = await get(
                    session,
                    url,
                    data={},
                    headers={}
                )
                if statusCode >= 400:
                    raise Exception(statusCode, response)
                return response
                # print('Salvo no banco de dados - notas_fiscais_nsu')
        except Exception as e:
            print('Error ao pegar DeParaECD')
            print(e)
