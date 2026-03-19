from qdrant_client import QdrantClient, models
c = QdrantClient('http://qdrant:6333')
try:
    res, _ = c.scroll(
        collection_name='gumaphoto_hybrid_kr',
        scroll_filter=models.Filter(
            must=[models.FieldCondition(key='filepath', match=models.MatchText(text='Unknown-Year'))]
        ),
        limit=5,
        with_payload=True
    )
    print("Files found with Unknown-Year:", len(res))
    for r in res:
        print(f"File: {r.payload.get('filepath')} | Date: {r.payload.get('date')} | Loc: {r.payload.get('location')}")
except Exception as e:
    print("Error:", e)
