#!/usr/bin/env python3
"""Create a project checkpoint for error recovery."""
import json, os, datetime, subprocess, sys

BASE = os.path.join(os.environ.get('USERPROFILE', '.'), 'Documents', 'Hermes Agent OS团队')
CHECKPOINT_DIR = os.path.join(BASE, '.hermes', 'checkpoints')
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

def get_git_hash():
    try:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'],
                               cwd=BASE, capture_output=True, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else None
    except: return None

checkpoint = {
    'id': f'checkpoint_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}',
    'timestamp': datetime.datetime.now().isoformat(),
    'git_hash': get_git_hash(),
    'type': sys.argv[1] if len(sys.argv) > 1 else 'MANUAL',
    'files_changed': sys.argv[2:] if len(sys.argv) > 2 else []
}

filepath = os.path.join(CHECKPOINT_DIR, f'{checkpoint["id"]}.json')
with open(filepath, 'w') as f:
    json.dump(checkpoint, f, indent=2)
print(f'Checkpoint saved: {filepath}')