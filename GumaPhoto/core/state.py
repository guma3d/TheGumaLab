class AppState:
    def __init__(self):
        self.qdrant_client = None
        self.siglip_processor = None
        self.siglip_model = None
        self.gemini_client = None
        self.known_faces = {}
        
        # Upload & Pipeline States
        self.upload_lock = None # threading.Lock()
        self.pipeline_running = False
        self.needs_rerun = False
        
        # Paths
        self.db_path = "/app/data/organizer_state.db"
        self.upload_dir = "/app/data/uploads_raw"
        self.organized_dir = "/app/data/organized"

state = AppState()
