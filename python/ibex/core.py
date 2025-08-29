# ibex/core.py
import os
from pathlib import Path
import json
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import hashlib
from .telemetry import TelemetryClient
from .git_integration import GitManager
from .llm import LLMManager
import asyncio

class IbexEventHandler(FileSystemEventHandler):
    def __init__(self, watcher):
        self.watcher = watcher
        
    def on_modified(self, event):
        if event.is_directory or '.ibex' in event.src_path:
            return
            
        self.watcher.handle_change(event.src_path)

class IbexWatcher:
    def __init__(self, path: str, intent: str = None):
        self.path = Path(path)
        self.ibex_dir = self.path / '.ibex'
        self.observer = Observer()
        self.handler = IbexEventHandler(self)
        self.telemetry = TelemetryClient()
        self.git = GitManager(path)
        self.llm = LLMManager(path)
        
        # Create .ibex directory if it doesn't exist
        if not self.ibex_dir.exists():
            self.ibex_dir.mkdir()
            self.save_state({
                'intent': intent,
                'stakes': [],
                'changes': []
            })
    
    def start(self):
        """Start watching for changes"""
        try:
            self.observer.schedule(self.handler, str(self.path), recursive=True)
            self.observer.start()
        except Exception as e:
            print(f"Error starting observer: {e}")
            self.stop()
    
    def stop(self):
        """Stop watching for changes"""
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
    
    def handle_change(self, file_path: str):
        """Handle a file change event"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create simple hash of content
            file_hash = hashlib.sha256(content.encode()).hexdigest()[:8]
            
            # Get current state
            state = self.load_state()
            
            # Record change
            change = {
                'file': file_path,
                'hash': file_hash,
                'timestamp': datetime.now().isoformat(),
                'summary': f"Changed {Path(file_path).name}"
            }
            
            # Only track files that are part of git repo
            if file_path in self.git.get_uncommitted_changes():
                state['changes'].append(change)
                self.save_state(state)
                self.telemetry.log_event("file_change", change)
            
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except Exception as e:
            print(f"Error handling change: {e}")
    
    async def create_stake(self, name: str, message: str):
        """Create a stake point with LLM-enhanced commit message"""
        state = self.load_state()
        
        # Get LLM analysis
        llm_message = await self.llm.analyze_changes(
            state['changes'],
            state.get('intent', '')
        )
        
        # Create commit with enhanced message
        changed_files = list(set([change['file'] for change in state['changes']]))
        if changed_files:
            self.git.stage_changes(changed_files)
            commit = self.git.commit(
                message=f"Stake: {name}",
                description=f"{message}\n\n{llm_message}"
            )
            
            # Store semantic information
            if commit:
                self.llm.store_semantic_change(
                    str(commit.hexsha),
                    llm_message,
                    state['changes'],
                    state.get('intent', '')
                )
        
        # Create stake
        stake = {
            'name': name,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'changes': state['changes'].copy()
        }
        
        state['stakes'].append(stake)
        state['changes'] = []  # Clear changes after creating stake
        self.save_state(state)
        self.telemetry.log_event("stake_created", stake)
    
    def save_state(self, state: dict):
        """Save IBEX state to disk"""
        with open(self.ibex_dir / 'state.json', 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self) -> dict:
        """Load IBEX state from disk"""
        try:
            with open(self.ibex_dir / 'state.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'intent': None, 'stakes': [], 'changes': []}