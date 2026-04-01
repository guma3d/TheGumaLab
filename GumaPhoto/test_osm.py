import httpx; import asyncio
async def t():
    res = await httpx.AsyncClient().get('https://nominatim.openstreetmap.org/search?q=에펠탑&format=jsonv2&limit=10&accept-language=ko', headers={'User-Agent': 'GumaPhoto-SearchApp/1.0'})
    print(res.json())
asyncio.run(t())
