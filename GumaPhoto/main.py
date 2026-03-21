import os
import subprocess
import pickle
import numpy as np
import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import threading

import torch
from transformers import AutoProcessor, AutoModel
from qdrant_client import QdrantClient
from google import genai
import sqlite3

# Import central State & Services
from core.state import state
from services.background_tasks import trigger_upload_pipeline, scheduled_scan

# Import Refactored Routers
from api.routers import views, upload, search, download, feedback, organizer, ai_indexer, delete, system

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    import sys
    
    # (legacy tracker and daemon processes were fully replaced by decoupled ORM API and Celery Event-Bus)
    
    # 2. Initialize SQLAlchemy Tables
    try:
        from core.database import engine
        from core.models import Base
        Base.metadata.create_all(bind=engine)
        print("[*] SQLAlchemy ORM Database schemas synchronized.")
    except Exception as e:
        print(f"[*] DB init error: {e}")
        
    # 3. Load Known Faces
    try:
        state.upload_lock = threading.Lock()
        
        if os.path.exists("/app/data/known_faces.pkl"):
            with open("/app/data/known_faces.pkl", "rb") as f:
                raw_faces = pickle.load(f)
                valid_faces = 0
                for name, vectors in raw_faces.items():
                    if vectors:
                        mean_vec = np.mean(vectors, axis=0)
                        mean_vec = mean_vec / np.linalg.norm(mean_vec)
                        state.known_faces[name] = mean_vec.tolist()
                        valid_faces += 1
            print(f"[*] Loaded {valid_faces} known faces from learning data.")
        else:
            print("[-] No known_faces.pkl found.")
    except Exception as e:
        print(f"[*] Error loading known_faces.pkl: {e}")

    # 4. Load AI Models
    try:
        print("[*] 🖼️ Loading High-End SigLIP (google/siglip-base-patch16-224)...")
        state.siglip_processor = AutoProcessor.from_pretrained('google/siglip-base-patch16-224')
        state.siglip_model = AutoModel.from_pretrained('google/siglip-base-patch16-224').to("cuda" if torch.cuda.is_available() else "cpu")
        state.siglip_model.eval()
    except Exception as e:
        print(f"[-] Failed to load SigLIP model: {e}")
    
    # 5. Load DB Clients
    print("[*] Connecting to Qdrant (http://qdrant:6333)...")
    state.qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL", "http://qdrant:6333"))
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        print("[*] Gemini API Key found. Initializing LLM Parser...")
        state.gemini_client = genai.Client(api_key=gemini_key)
    else:
        print("[!] No GEMINI_API_KEY found. LLM Natural Language Parser is disabled.")
        
    # 6. Start Autonomous Scheduled Scanner
    scan_task = asyncio.create_task(scheduled_scan(3600))
        
    yield
    
    print("[*] Shutting down GumaPhoto logic...")
    scan_task.cancel()

app = FastAPI(title="GumaPhoto API", lifespan=lifespan)

# --- frontend assets ---
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")
app.mount("/photos", StaticFiles(directory="/app/data/organized"), name="photos")

# --- routers (Domain-Driven Endpoints) ---
app.include_router(views.router, tags=["Views"])
app.include_router(upload.router, tags=["Upload"])
app.include_router(search.router, tags=["Search"])
app.include_router(download.router, tags=["Download"])
app.include_router(feedback.router, tags=["Feedback"])
app.include_router(organizer.router, tags=["Organizer"])
app.include_router(ai_indexer.router, tags=["AI_Indexer"])
app.include_router(delete.router, tags=["Delete_Photo"])
app.include_router(system.router, prefix="/api/system", tags=["System"])
