#!/usr/bin/env python3
import json
from datetime import datetime
import hashlib
import os
import subprocess

# Read current state
with open('.ibex/state.json', 'r') as f:
    state = json.load(f)

# Get modified files
result = subprocess.run(['git', 'diff', '--name-only'], capture_output=True, text=True)
modified_files = result.stdout.strip().split('\n') if result.stdout.strip() else []

print(f"Found {len(modified_files)} modified files: {modified_files}")

# Add changes to state
for file_path in modified_files:
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            file_hash = hashlib.sha256(content.encode()).hexdigest()[:8]
            change = {
                'file': file_path,
                'hash': file_hash,
                'timestamp': datetime.now().isoformat(),
                'summary': f'Changed {os.path.basename(file_path)}'
            }
            state['changes'].append(change)
            print(f"Added change for {file_path}")
        except Exception as e:
            print(f'Error reading {file_path}: {e}')

# Save updated state
with open('.ibex/state.json', 'w') as f:
    json.dump(state, f, indent=2)

print(f'Added {len(modified_files)} changes to IBEX state')
