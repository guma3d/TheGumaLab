import torch
from transformers import AutoProcessor, AutoModel
import numpy as np

class SigLIPEngine:
    def __init__(self):
        print("[*] 🖼️ 초정밀 SigLIP 이미지 인코더 로드 중 (google/siglip-base-patch16-224) ...")
        self.processor = AutoProcessor.from_pretrained("google/siglip-base-patch16-224")
        self.model = AutoModel.from_pretrained("google/siglip-base-patch16-224", torch_dtype=torch.float16).to('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.eval()

    def infer_batch(self, pil_images):
        scene_embeddings = [None] * len(pil_images)
        try:
            inputs = self.processor(images=pil_images, return_tensors="pt").to(self.model.device)
            inputs = {k: v.to(torch.float16) if v.dtype in (torch.float32, torch.float) else v for k, v in inputs.items()}
            with torch.no_grad():
                out = self.model.get_image_features(**inputs)
                emb = out / out.norm(p=2, dim=-1, keepdim=True)
                scene_embeddings = emb.cpu().numpy()
        except Exception as e:
            print(f"      🚨 SigLIP 연산 오류: {e}")
            
        return scene_embeddings
