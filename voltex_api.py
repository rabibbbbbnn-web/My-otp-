import aiohttp
from config import VOLTEX_API_URL

async def get_sms_number(api_key, service, country="bd"):
    url = f"{VOLTEX_API_URL}/number?api_key={api_key}&service={service}&country={country}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data
            return None

async def check_sms(api_key, order_id):
    url = f"{VOLTEX_API_URL}/status?api_key={api_key}&order_id={order_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data
            return None
