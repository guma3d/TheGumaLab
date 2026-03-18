import inspect
from hsemotion.facial_emotions import get_model_path
source_lines = inspect.getsourcelines(get_model_path)[0]
for line in source_lines:
    print(line, end='')
