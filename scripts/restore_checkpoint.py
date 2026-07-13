#!/usr/bin/env python3
"""Restore from a project checkpoint."""
import json, os, subprocess, sys, glob

BASE = os.path.join(os.environ.get('USERPROFILE', '.'), 'Documents', 'Hermes Agent OS团队')
CHECKPOINT_DIR = os.path.join(BASE, '.hermes', 'checkpoints')

def list_checkpoints():
    files = sorted(glob.glob(os.path.join(CHECKPOINT_DIR, 'checkpoint_*.json')))
    for f in files[-10:]:
        with open(f) as fh:
            cp = json.load(fh)
        print(f'  {cp["id"]} | {cp["timestamp"]} | type={cp["type"]} | git={cp["git_hash"] or "N/A"}')

def restore(checkpoint_id):
    fp = os.path.join(CHECKPOINT_DIR, f'{checkpoint_id}.json')
    if not os.path.exists(fp):
        print(f'Checkpoint not found: {checkpoint_id}')
        return False
    with open(fp) as f:
        cp = json.load(f)
    if cp.get('git_hash'):
        subprocess.run(['git', 'reset', '--hard', cp['git_hash']], cwd=BASE)
        print(f'Restored to git commit: {cp["git_hash"]}')
    else:
        print('No git hash in checkpoint, manual restore needed')
    return True

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'list':
        list_checkpoints()
    elif len(sys.argv) > 2 and sys.argv[1] == 'restore':
        restore(sys.argv[2])
    else:
        print('Usage: restore_checkpoint.py list | restore <checkpoint_id>')