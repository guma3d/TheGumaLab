import pickle
import os
import glob
import cv2
from insightface.app import FaceAnalysis

f = '/app/data/known_faces.pkl'
if os.path.exists(f):
    data = pickle.load(open(f, 'rb'))
    print(f"Persons in known_faces.pkl: {list(data.keys())}")
else:
    print("known_faces.pkl NOT FOUND")

# Check enrolled directory
enrolled_dir = "/app/data/enrolled"
if os.path.exists(enrolled_dir):
    print("Enrolled folders:")
    for person in os.listdir(enrolled_dir):
        files = glob.glob(f"{enrolled_dir}/{person}/*.jpg")
        print(f" - {person}: {len(files)} chip images")
        
        # Try to detect with InsightFace to prove theory
        face_app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        face_app.prepare(ctx_id=0, det_size=(640, 640))
        success = 0
        for p in files[:5]:
            img = cv2.imread(p)
            if img is not None:
                faces = face_app.get(img)
                if faces: success += 1
        print(f"   -> InsightFace detected face in {success}/{min(5, len(files))} test chips.")
