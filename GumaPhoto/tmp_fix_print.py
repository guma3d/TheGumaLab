import os

path = r'd:\TheGumaLab\GumaPhoto\api\services\feedback_cache.py'
code = open(path, 'r', encoding='utf-8').read()

target = 'print(f"🎉 [FeedbackCache] Generated Top {len(final_queue)} clusters in {time.time()-start_t:.2f}s!", flush=True)'
repl = 'print(f"🎉 [FeedbackCache] Generated Top {len(final_queue)} clusters in {time.time()-start_t:.2f}s! (Top 1 has {final_queue[0].get(\'match_count\')} photos)" if final_queue else "🎉 Generated 0 clusters", flush=True)'

open(path, 'w', encoding='utf-8').write(code.replace(target, repl))
print("Print updated.")
