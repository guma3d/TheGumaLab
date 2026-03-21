import torch
import warnings
from transformers import AutoModelForCausalLM, AutoProcessor
warnings.filterwarnings("ignore")

class FlorenceEngine:
    def __init__(self):
        print("[*] 📝 Florence-2-base VLM 상황 묘사 AI 로드 중 ...")
        try:
            florence_model_id = "microsoft/Florence-2-base"
            self.model = AutoModelForCausalLM.from_pretrained(florence_model_id, trust_remote_code=True, torch_dtype=torch.bfloat16).to("cuda" if torch.cuda.is_available() else "cpu")
            self.processor = AutoProcessor.from_pretrained(florence_model_id, trust_remote_code=True)
            self.model.eval()
            print("  [+] Florence-2-base 로드 완료!")
        except Exception as e:
            print(f"  [-] Florence-2-base 로딩 실패: {e}")
            self.model = None

    def infer_batch(self, pil_images):
        captions_batch = [""] * len(pil_images)
        objects_batch = [[] for _ in pil_images]
        if not self.model: 
            return captions_batch, objects_batch
            
        try:
            # 캡션 다중 배치
            task_prompt_cap = "<MORE_DETAILED_CAPTION>"
            flo_inputs_cap = self.processor(text=[task_prompt_cap]*len(pil_images), images=pil_images, return_tensors="pt").to(self.model.device)
            flo_inputs_cap = {k: v.to(torch.bfloat16) if v.dtype in (torch.float32, torch.float) else v for k, v in flo_inputs_cap.items()}
            with torch.no_grad():
                generated_ids_cap = self.model.generate(
                    input_ids=flo_inputs_cap["input_ids"],
                    pixel_values=flo_inputs_cap["pixel_values"],
                    max_new_tokens=256, early_stopping=True, do_sample=False, num_beams=1, repetition_penalty=1.5
                )
            generated_texts_cap = self.processor.batch_decode(generated_ids_cap, skip_special_tokens=False)
            for idx, text in enumerate(generated_texts_cap):
                parsed = self.processor.post_process_generation(text, task=task_prompt_cap, image_size=(pil_images[idx].width, pil_images[idx].height))
                captions_batch[idx] = parsed.get(task_prompt_cap, "")
                
            # 사물 태그 다중 배치
            task_prompt_od = "<OD>"
            flo_inputs_od = self.processor(text=[task_prompt_od]*len(pil_images), images=pil_images, return_tensors="pt").to(self.model.device)
            flo_inputs_od = {k: v.to(torch.bfloat16) if v.dtype in (torch.float32, torch.float) else v for k, v in flo_inputs_od.items()}
            with torch.no_grad():
                generated_ids_od = self.model.generate(
                    input_ids=flo_inputs_od["input_ids"],
                    pixel_values=flo_inputs_od["pixel_values"],
                    max_new_tokens=256, early_stopping=True, do_sample=False, num_beams=1, repetition_penalty=1.5
                )
            generated_texts_od = self.processor.batch_decode(generated_ids_od, skip_special_tokens=False)
            for idx, text in enumerate(generated_texts_od):
                parsed = self.processor.post_process_generation(text, task=task_prompt_od, image_size=(pil_images[idx].width, pil_images[idx].height))
                od_res = parsed.get(task_prompt_od, {})
                obj_list = []
                if isinstance(od_res, dict) and "labels" in od_res:
                    for label in od_res["labels"]:
                        clean_label = str(label).strip().lower()
                        if clean_label and "person" not in clean_label and clean_label not in obj_list:
                            obj_list.append(clean_label)
                objects_batch[idx] = obj_list
        except Exception as e:
            print(f"      ⚠️ Florence-2 다중 배치 처리 중 오류: {e}")
            
        return captions_batch, objects_batch
