from qdrant_client import QdrantClient
from qdrant_client.http.models import PayloadSchemaType
import time

def patch_db():
    print("[*] Connecting to Qdrant...")
    client = QdrantClient("http://qdrant:6333")
    collection = "gumaphoto_hybrid_kr"
    
    print("[*] Creating GEO index for 'geo_point'...")
    try:
        client.create_payload_index(collection, "geo_point", field_schema=PayloadSchemaType.GEO)
        print("  [+] GEO index created successfully.")
    except Exception as e:
        print(f"  [!] GEO index might exist: {e}")

    print("[*] Patching payloads to include proper geo_point...")
    offset = None
    count = 0
    while True:
        records, offset = client.scroll(collection_name=collection, limit=500, offset=offset)
        for r in records:
            p = r.payload or {}
            # If lat/lon exist but no geo_point, fix it
            if p.get("lat") is not None and p.get("lon") is not None:
                if "geo_point" not in p:
                    p["geo_point"] = {"lat": float(p["lat"]), "lon": float(p["lon"])}
                    client.set_payload(collection_name=collection, payload={"geo_point": p["geo_point"]}, points=[r.id])
                    count += 1
        print(f"  ... processed chunk. Patched {count} photos so far.")
        if offset is None:
            break
            
    print(f"\n[+] Successfully patched {count} photos with valid GPS data! Qdrant GeoRadius is now fully functional.")

if __name__ == '__main__':
    patch_db()
