from api.services.theme_service import state
from qdrant_client import QdrantClient
from transformers import AutoProcessor, AutoModel
import torch

state.qdrant_client = QdrantClient(url="http://qdrant:6333")
processor = AutoProcessor.from_pretrained("google/siglip-base-patch16-224")
model = AutoModel.from_pretrained("google/siglip-base-patch16-224")

inputs = processor(text=["desert sand dune dry heat barren arid"], padding="max_length", return_tensors="pt")
with torch.no_grad():
    text_features = model.get_text_features(**inputs)
    text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
    text_vector = text_features[0].cpu().numpy().tolist()

results = state.qdrant_client.query_points(
    collection_name="gumaphoto_hybrid_kr",
    query=text_vector,
    using="scene",
    limit=5
).points

for r in results:
    print(r.score)

