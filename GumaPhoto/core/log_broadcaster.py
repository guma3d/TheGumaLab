import sys
import os
import redis
import logging
from datetime import datetime

class RedisStdoutWrapper:
    def __init__(self, prefix="[APP]"):
        self.original_stdout = sys.stdout
        self.prefix = prefix
        self.buffer = ""
        self.r = None
        try:
            self.r = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)
        except Exception as e:
            pass

    def write(self, message):
        self.original_stdout.write(message)
        self.original_stdout.flush()
        
        if not self.r:
            return

        self.buffer += message
        if '\n' in self.buffer:
            lines = self.buffer.split('\n')
            for line in lines[:-1]:
                clean_line = line.strip()
                if clean_line:
                    # Time Prefix for context
                    now = datetime.now().strftime("%H:%M:%S")
                    full_message = f"[{now}] {self.prefix} {clean_line}"
                    try:
                        self.r.rpush("gumaphoto_logs_history", full_message)
                        self.r.ltrim("gumaphoto_logs_history", -50, -1)  # Keep only last 50 lines
                        self.r.publish("gumaphoto_logs_channel", full_message)
                    except Exception:
                        pass
            self.buffer = lines[-1]

    def flush(self):
        self.original_stdout.flush()

def setup_unified_logging(prefix="[APP]"):
    sys.stdout = RedisStdoutWrapper(prefix)
    # Also redirect stderr
    sys.stderr = sys.stdout
