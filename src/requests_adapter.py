from typing import Dict
from aiohttp import ClientSession


async def get(session: ClientSession, url: str, data: Dict[str, str], headers: Dict[str, str]):
    async with session.get(url, json=data, headers=headers) as response:
        data = await response.json()
        return data, response.status


async def getWithoudData(session: ClientSession, url: str, headers: Dict[str, str]):
    async with session.get(url, headers=headers) as response:
        data = await response.json()
        return data, response.status, response.headers


async def post(session: ClientSession, url: str, data: Dict[str, str], headers: Dict[str, str]):
    async with session.post(url, data=data, headers=headers) as response:
        data = await response.json()
        return data, response.status


async def put(session: ClientSession, url: str, data: Dict[str, str], headers: Dict[str, str]):
    async with session.put(url, data=data, headers=headers) as response:
        data = await response.json()
        return data, response.status


async def patch(session: ClientSession, url: str, data: Dict[str, str], headers: Dict[str, str]):
    async with session.patch(url, data=data, headers=headers) as response:
        data = await response.json()
        return data, response.status
