import sys
sys.path.append("/app")
from api.services.theme_service import build_timeline_cache_only
build_timeline_cache_only()
