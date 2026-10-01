"""Shared production context and traceable feedback revision for all products."""
import json
import hashlib
from pathlib import Path

RULES_PATH = Path(__file__).with_name('production_rules.json')


def snapshot(category):
    data = json.loads(RULES_PATH.read_text(encoding='utf-8'))
    rules = [r for r in data['rules'] if r['category'] in ('all', category)]
    return dict(revision=data['revision'], category=category, rules=rules,
        sha256=hashlib.sha256(RULES_PATH.read_bytes()).hexdigest())


def prompt_context(category):
    data = snapshot(category)
    return '\nShared production requirements (' + data['revision'] + '):\n' + '\n'.join(
        '- ' + r['instruction'] for r in data['rules'])
