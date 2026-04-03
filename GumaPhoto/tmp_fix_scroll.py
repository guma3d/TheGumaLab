import sys

code = open('d:/TheGumaLab/GumaPhoto/api/services/feedback_cache.py', 'r', encoding='utf-8').read()

target = """            unknowns, _ = state.qdrant_client.scroll(
                collection_name="gumaphoto_hybrid_kr",
                scroll_filter=Filter(
                    should=[
                        FieldCondition(key="date", match=MatchText(text="Unknown")),
                        FieldCondition(key="location", match=MatchText(text="Unknown")),
                        FieldCondition(key="location", match=MatchText(text="위치정보없음")),
                        FieldCondition(key="people", match=MatchValue(value="Unknown Person")),
                        FieldCondition(key="people", match=MatchValue(value="Unknown People"))
                    ]
                ),
                limit=3000,
                with_payload=True,
                with_vectors=False
            )"""

replacement = """            unknowns = []
            next_page_offset = None
            scroll_filter = Filter(
                should=[
                    FieldCondition(key="date", match=MatchText(text="Unknown")),
                    FieldCondition(key="location", match=MatchText(text="Unknown")),
                    FieldCondition(key="location", match=MatchText(text="위치정보없음")),
                    FieldCondition(key="people", match=MatchValue(value="Unknown Person")),
                    FieldCondition(key="people", match=MatchValue(value="Unknown People"))
                ]
            )
            while True:
                batch, next_page_offset = state.qdrant_client.scroll(
                    collection_name="gumaphoto_hybrid_kr",
                    scroll_filter=scroll_filter,
                    limit=5000,
                    offset=next_page_offset,
                    with_payload=True,
                    with_vectors=False
                )
                unknowns.extend(batch)
                if next_page_offset is None or len(unknowns) >= 30000:
                    break"""

new_code = code.replace(target, replacement)
new_code = new_code.replace('candidates = candidates[:300]', 'candidates = candidates[:500]')
new_code = new_code.replace('limit=100,', 'limit=300,')

open('d:/TheGumaLab/GumaPhoto/api/services/feedback_cache.py', 'w', encoding='utf-8').write(new_code)
print("Updated successfully")
