from api.services.theme_service import build_theme_cache
import os
os.environ["QDRANT_URL"] = "http://gumaphoto_qdrant:6333"
build_theme_cache()
print("Themes baked successfully!")
