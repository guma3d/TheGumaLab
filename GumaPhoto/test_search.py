import asyncio
from api.routers.search import perform_search, SearchRequest

async def main():
    req = SearchRequest(query='강원도 사진', offset=0, limit=1)
    res = await perform_search(req)
    print("TOTAL HITS:", res.get("total_hits"))
    print("RESULTS EXAMPLES:", [(r['location'], r['date']) for r in res.get("results", [])])

if __name__ == "__main__":
    asyncio.run(main())
