# ibex/core.py
import os
from pathlib import Path
import json
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import hashlib
from functools import lru_cache
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

        # LRU Cache configuration
        self._file_hash_cache = {}
        self._file_content_cache = {}
        self._git_status_cache = None
        self._git_status_timestamp = None
        self._state_cache = None
        self._state_timestamp = None
        self._cache_max_age = 30  # seconds

        # Create .ibex directory if it doesn't exist
        if not self.ibex_dir.exists():
            self.ibex_dir.mkdir()
            self.save_state({
                'intent': intent,
                'stakes': [],
                'changes': []
            })

    def _is_cache_expired(self, timestamp: datetime) -> bool:
        """Check if cache entry has expired"""
        if timestamp is None:
            return True
        return (datetime.now() - timestamp).seconds > self._cache_max_age

    def _invalidate_file_cache(self, file_path: str):
        """Invalidate cache entries for a specific file"""
        if file_path in self._file_hash_cache:
            del self._file_hash_cache[file_path]
        if file_path in self._file_content_cache:
            del self._file_content_cache[file_path]

    def _clear_expired_cache(self):
        """Clear expired cache entries"""
        # Git status cache
        if self._git_status_timestamp and self._is_cache_expired(self._git_status_timestamp):
            self._git_status_cache = None
            self._git_status_timestamp = None

        # State cache
        if self._state_timestamp and self._is_cache_expired(self._state_timestamp):
            self._state_cache = None
            self._state_timestamp = None

    def _get_cached_file_hash(self, file_path: str) -> str:
        """Get cached file hash or compute and cache it"""
        try:
            # Check cache first
            if file_path in self._file_hash_cache:
                cache_entry = self._file_hash_cache[file_path]
                if not self._is_cache_expired(cache_entry['timestamp']):
                    return cache_entry['hash']

            # Compute hash
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            file_hash = hashlib.sha256(content.encode()).hexdigest()[:8]

            # Cache the result
            self._file_hash_cache[file_path] = {
                'hash': file_hash,
                'timestamp': datetime.now()
            }

            return file_hash

        except (FileNotFoundError, UnicodeDecodeError):
            # For binary files or missing files, return a special hash
            return "binary"

    def _get_cached_git_status(self):
        """Get cached git status or fetch and cache it"""
        self._clear_expired_cache()

        if self._git_status_cache is not None and not self._is_cache_expired(self._git_status_timestamp):
            return self._git_status_cache

        # Fetch fresh git status
        self._git_status_cache = self.git.get_uncommitted_changes()
        self._git_status_timestamp = datetime.now()

        return self._git_status_cache

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
        """Handle a file change event with caching"""
        try:
            # Invalidate cache for this file
            self._invalidate_file_cache(file_path)

            # Get cached file hash
            file_hash = self._get_cached_file_hash(file_path)

            # Get current state
            state = self.load_state()

            # Record change
            change = {
                'file': file_path,
                'hash': file_hash,
                'timestamp': datetime.now().isoformat(),
                'summary': f"Changed {Path(file_path).name}"
            }

            # Only track files that are part of git repo (using cached git status)
            git_changes = self._get_cached_git_status()
            if file_path in git_changes:
                state['changes'].append(change)
                self.save_state(state)
                self.telemetry.log_event("file_change", change)

        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except Exception as e:
            print(f"Error handling change: {e}")
    
    def detect_current_changes(self):
        """Detect all current uncommitted changes and add them to the change log with caching"""
        state = self.load_state()

        # Get all uncommitted changes from git (using cached version)
        uncommitted_files = self._get_cached_git_status()

        print(f"Detected {len(uncommitted_files)} uncommitted files")

        for file_path in uncommitted_files:
            try:
                # Check if this change is already tracked
                already_tracked = any(change['file'] == file_path for change in state['changes'])

                if not already_tracked:
                    # Get cached file hash
                    file_hash = self._get_cached_file_hash(file_path)

                    # Add change to state
                    change = {
                        'file': file_path,
                        'hash': file_hash,
                        'timestamp': datetime.now().isoformat(),
                        'summary': f"Changed {Path(file_path).name}"
                    }

                    state['changes'].append(change)
                    print(f"Added to change log: {file_path}")

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

        self.save_state(state)
        return len(state['changes'])

    async def create_stake(self, name: str, message: str, auto_detect: bool = True):
        """Create a stake point with LLM-enhanced commit message"""
        state = self.load_state()
        
        # If auto_detect is True and we have no tracked changes, detect current changes
        if auto_detect and not state['changes']:
            print("No tracked changes found, detecting current uncommitted changes...")
            self.detect_current_changes()
            state = self.load_state()  # Reload state after detection
        
        if not state['changes']:
            print("No changes to commit")
            return
        
        print(f"Processing {len(state['changes'])} changes for stake...")
        
        # Get LLM analysis
        llm_message = await self.llm.analyze_changes(
            state['changes'],
            state.get('intent', '')
        )
        
        # Create commit with enhanced message
        changed_files = list(set([change['file'] for change in state['changes']]))
        if changed_files:
            print(f"Staging {len(changed_files)} files...")
            
            # Stage all changes first
            self.git.stage_all_changes()
            
            commit = self.git.commit(
                message=f"Stake: {name}",
                description=f"{message}\n\n{llm_message}"
            )
            
            if commit:
                print(f"Successfully created commit: {commit.hexsha[:8]}")
                
                # Store semantic information
                self.llm.store_semantic_change(
                    str(commit.hexsha),
                    llm_message,
                    state['changes'],
                    state.get('intent', '')
                )
            else:
                print("Failed to create commit")
        
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
        """Save IBEX state to disk with cache invalidation"""
        with open(self.ibex_dir / 'state.json', 'w') as f:
            json.dump(state, f, indent=2)

        # Invalidate cache
        self._state_cache = None
        self._state_timestamp = None

    def load_state(self) -> dict:
        """Load IBEX state from disk with caching"""
        self._clear_expired_cache()

        # Check cache first
        if self._state_cache is not None and not self._is_cache_expired(self._state_timestamp):
            return self._state_cache.copy()

        # Load from disk
        try:
            with open(self.ibex_dir / 'state.json', 'r') as f:
                state = json.load(f)
        except FileNotFoundError:
            state = {'intent': None, 'stakes': [], 'changes': []}

        # Cache the result
        self._state_cache = state.copy()
        self._state_timestamp = datetime.now()

        return state