import os
import re

path = r'd:\TheGumaLab\GumaPhoto\api\services\feedback_cache.py'
code = open(path, 'r', encoding='utf-8').read()

if 'import json' not in code:
    code = code.replace('import time', 'import time\nimport json\nimport os\n\nclass MockRaw:\n    def __init__(self, id, payload):\n        self.id = id\n        self.payload = payload')

new_class_methods = """
    def save_to_disk(self):
        try:
            os.makedirs('data', exist_ok=True)
            export_list = []
            for item in self.queue:
                export_list.append({
                    "id": str(item["raw"].id),
                    "payload": item["raw"].payload,
                    "issue": item["issue"],
                    "match_count": item["match_count"],
                    "unresolved_ids": list(item["unresolved_ids"])
                })
            with open('data/feedback_queue.json', 'w', encoding='utf-8') as f:
                json.dump(export_list, f, ensure_ascii=False)
            print("[FeedbackCache] 💾 Successfully saved queue to disk persistence.", flush=True)
        except Exception as e:
            print(f"❌ Failed to save disk cache: {e}")

    def load_from_disk(self):
        try:
            if os.path.exists('data/feedback_queue.json'):
                with open('data/feedback_queue.json', 'r', encoding='utf-8') as f:
                    import_list = json.load(f)
                new_queue = []
                for entry in import_list:
                    new_queue.append({
                        "raw": MockRaw(entry["id"], entry["payload"]),
                        "issue": entry["issue"],
                        "match_count": entry["match_count"],
                        "unresolved_ids": set(entry["unresolved_ids"])
                    })
                self.queue = new_queue
                print(f"[FeedbackCache] 💾 Successfully loaded {len(self.queue)} items from disk.", flush=True)
                return True
        except Exception as e:
            print(f"❌ Failed to load disk cache: {e}")
        return False
"""

# inject methods before pop_best
if 'def save_to_disk' not in code:
    code = code.replace('    def pop_best(self):', new_class_methods + '\n    def pop_best(self):')

# modify build worker to save
if 'self.queue = final_queue' in code and 'self.save_to_disk()' not in code:
    code = code.replace('self.queue = final_queue', 'self.queue = final_queue\n                self.save_to_disk()')

# modify remove_processed to save
if 'self.queue = new_queue' in code and 'self.save_to_disk()' not in code.split('def remove_processed')[-1]:
    code = code.replace('self.queue = new_queue\n            print(', 'self.queue = new_queue\n            self.save_to_disk()\n            print(')

# load from disk in init
init_target = """        self.queue = []
        self.is_building = False
        self.lock = threading.RLock()"""
init_repl = """        self.queue = []
        self.is_building = False
        self.lock = threading.RLock()
        self.load_from_disk()"""

if 'self.load_from_disk()' not in code:
    code = code.replace(init_target, init_repl)

open(path, 'w', encoding='utf-8').write(code)
print("Disk cache patch applied!")
