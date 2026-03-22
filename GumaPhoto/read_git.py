import subprocess
import builtins
import sys

# Get log output
res = subprocess.run(['git', 'log', '-p', 'api/services/feedback_service.py'], capture_output=True)

with open('git_history_utf8.txt', 'wb') as f:
    f.write(res.stdout)
