from api.services.theme_service import app_startup_task
from core.state import state
from qdrant_client import QdrantClient
import asyncio

state.qdrant_client = QdrantClient(url="http://gumaphoto_qdrant:6333")
asyncio.run(app_startup_task())
print("Themes baked successfully!")
