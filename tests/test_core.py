"""
Comprehensive tests for IBEX core module (IbexWatcher)

Tests cover:
- File watching functionality
- State management and persistence
- Caching mechanisms (file hash, git status, state)
- Change detection and tracking
- Stake creation
- Integration with GitManager and LLMManager
"""

import pytest
import tempfile
import os
import sys
import time
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from git import Repo
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from ibex.core import IbexWatcher, IbexEventHandler


class TestIbexWatcherInitialization:
    """Test IbexWatcher initialization"""

    def test_init_creates_ibex_directory(self):
        """Test that initialization creates .ibex directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir, intent="Test intent")

            ibex_dir = Path(temp_dir) / '.ibex'
            assert ibex_dir.exists(), ".ibex directory should be created"

    def test_init_creates_state_file(self):
        """Test that initialization creates state.json file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir, intent="Test intent")

            state_file = Path(temp_dir) / '.ibex' / 'state.json'
            assert state_file.exists(), "state.json should be created"

    def test_init_with_intent(self):
        """Test initialization with intent"""
        with tempfile.TemporaryDirectory() as temp_dir:
            intent = "Implement authentication feature"
            watcher = IbexWatcher(temp_dir, intent=intent)

            state = watcher.load_state()
            assert state['intent'] == intent

    def test_init_creates_required_components(self):
        """Test that all required components are initialized"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir)

            assert watcher.observer is not None
            assert watcher.handler is not None
            assert watcher.telemetry is not None
            assert watcher.git is not None
            assert watcher.llm is not None

    def test_init_initializes_caches(self):
        """Test that caches are initialized"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir)

            assert watcher._file_hash_cache == {}
            assert watcher._file_content_cache == {}
            assert watcher._git_status_cache is None
            assert watcher._state_cache is None


class TestStateManagement:
    """Test state loading and saving"""

    def test_save_and_load_state(self):
        """Test saving and loading state"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir)

            state = {
                'intent': 'Test',
                'stakes': [{'name': 'stake1', 'message': 'First stake'}],
                'changes': [{'file': 'test.py', 'hash': 'abc123'}]
            }

            watcher.save_state(state)
            loaded_state = watcher.load_state()

            assert loaded_state['intent'] == 'Test'
            assert len(loaded_state['stakes']) == 1
            assert len(loaded_state['changes']) == 1

    def test_load_state_when_file_missing(self):
        """Test loading state when file doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create watcher but delete state file
            watcher = IbexWatcher(temp_dir)
            state_file = Path(temp_dir) / '.ibex' / 'state.json'
            state_file.unlink()

            state = watcher.load_state()

            # Should return default state
            assert state == {'intent': None, 'stakes': [], 'changes': []}

    def test_save_state_invalidates_cache(self):
        """Test that saving state invalidates cache"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir)

            # Load state to populate cache
            state1 = watcher.load_state()
            assert watcher._state_cache is not None

            # Save new state
            new_state = {'intent': 'New', 'stakes': [], 'changes': []}
            watcher.save_state(new_state)

            # Cache should be invalidated
            assert watcher._state_cache is None

    def test_state_persistence_across_instances(self):
        """Test that state persists across different watcher instances"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create first watcher and save state
            watcher1 = IbexWatcher(temp_dir)
            state = {
                'intent': 'Persistent test',
                'stakes': [],
                'changes': [{'file': 'test.py'}]
            }
            watcher1.save_state(state)

            # Create second watcher and load state
            watcher2 = IbexWatcher(temp_dir)
            loaded_state = watcher2.load_state()

            assert loaded_state['intent'] == 'Persistent test'
            assert len(loaded_state['changes']) == 1


class TestCachingMechanisms:
    """Test caching functionality"""

    def test_file_hash_caching(self):
        """Test that file hashes are cached"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir)

            # Create a test file
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("print('hello')")

            # Get hash twice
            hash1 = watcher._get_cached_file_hash(str(test_file))
            hash2 = watcher._get_cached_file_hash(str(test_file))

            assert hash1 == hash2
            assert str(test_file) in watcher._file_hash_cache

    def test_file_hash_cache_invalidation(self):
        """Test that file cache is invalidated on change"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir)

            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("original content")

            # Cache the hash
            hash1 = watcher._get_cached_file_hash(str(test_file))

            # Invalidate cache
            watcher._invalidate_file_cache(str(test_file))

            assert str(test_file) not in watcher._file_hash_cache

    def test_git_status_caching(self):
        """Test that git status is cached"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize git repo
            Repo.init(temp_dir)

            watcher = IbexWatcher(temp_dir)

            # Mock git.get_uncommitted_changes
            watcher.git.get_uncommitted_changes = Mock(return_value=['file1.py', 'file2.py'])

            # Get status twice
            status1 = watcher._get_cached_git_status()
            status2 = watcher._get_cached_git_status()

            # Should only call the actual method once (second is cached)
            assert watcher.git.get_uncommitted_changes.call_count == 1
            assert status1 == status2

    def test_git_status_cache_expiration(self):
        """Test that git status cache expires after timeout"""
        with tempfile.TemporaryDirectory() as temp_dir:
            Repo.init(temp_dir)
            watcher = IbexWatcher(temp_dir)

            # Set short cache timeout for testing
            watcher._cache_max_age = 0.1  # 100ms

            watcher.git.get_uncommitted_changes = Mock(return_value=['file1.py'])

            # Get status
            status1 = watcher._get_cached_git_status()

            # Wait for cache to expire
            time.sleep(0.2)

            # Get status again
            status2 = watcher._get_cached_git_status()

            # Should call method twice (cache expired)
            assert watcher.git.get_uncommitted_changes.call_count == 2

    def test_state_caching(self):
        """Test that state is cached"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir)

            # Load state twice
            state1 = watcher.load_state()
            state2 = watcher.load_state()

            # Should use cache (verify by checking cache is populated)
            assert watcher._state_cache is not None

    def test_cache_expiration_clearing(self):
        """Test that expired caches are cleared"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir)
            watcher._cache_max_age = 0.1  # 100ms

            # Populate caches
            watcher._git_status_cache = ['test.py']
            watcher._git_status_timestamp = datetime.now()
            watcher._state_cache = {'test': 'data'}
            watcher._state_timestamp = datetime.now()

            # Wait for expiration
            time.sleep(0.2)

            # Clear expired
            watcher._clear_expired_cache()

            assert watcher._git_status_cache is None
            assert watcher._state_cache is None


class TestChangeDetection:
    """Test change detection and tracking"""

    def test_handle_change_for_tracked_file(self):
        """Test handling change for a git-tracked file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize git repo
            repo = Repo.init(temp_dir)

            # Create and track a file
            test_file = Path(temp_dir) / "tracked.py"
            test_file.write_text("original")
            repo.index.add(["tracked.py"])
            repo.index.commit("Initial commit")

            watcher = IbexWatcher(temp_dir)

            # Modify the file
            test_file.write_text("modified")

            # Handle the change
            watcher.handle_change(str(test_file))

            # Check that change was recorded
            state = watcher.load_state()
            assert len(state['changes']) > 0
            assert any(str(test_file) in change['file'] for change in state['changes'])

    def test_handle_change_ignores_untracked_files(self):
        """Test that untracked files are not recorded"""
        with tempfile.TemporaryDirectory() as temp_dir:
            Repo.init(temp_dir)
            watcher = IbexWatcher(temp_dir)

            # Create untracked file
            test_file = Path(temp_dir) / "untracked.py"
            test_file.write_text("content")

            # Mock git status to return empty (no uncommitted changes)
            watcher.git.get_uncommitted_changes = Mock(return_value=[])

            watcher.handle_change(str(test_file))

            # Should not record change
            state = watcher.load_state()
            assert len(state['changes']) == 0

    def test_handle_change_ignores_ibex_directory(self):
        """Test that changes in .ibex directory are ignored"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir)

            # Create file in .ibex
            ibex_file = Path(temp_dir) / '.ibex' / 'test.txt'
            ibex_file.write_text("content")

            initial_changes = len(watcher.load_state()['changes'])

            watcher.handle_change(str(ibex_file))

            # Should not add change
            assert len(watcher.load_state()['changes']) == initial_changes

    def test_detect_current_changes(self):
        """Test detecting all current uncommitted changes"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize git repo
            repo = Repo.init(temp_dir)

            # Create and commit files
            for i in range(3):
                file_path = Path(temp_dir) / f"file{i}.py"
                file_path.write_text(f"content {i}")
                repo.index.add([f"file{i}.py"])

            repo.index.commit("Initial commit")

            # Modify all files
            for i in range(3):
                file_path = Path(temp_dir) / f"file{i}.py"
                file_path.write_text(f"modified {i}")

            watcher = IbexWatcher(temp_dir)

            # Detect changes
            count = watcher.detect_current_changes()

            assert count == 3
            state = watcher.load_state()
            assert len(state['changes']) == 3

    def test_detect_current_changes_avoids_duplicates(self):
        """Test that detect_current_changes doesn't add duplicates"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Repo.init(temp_dir)

            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("original")
            repo.index.add(["test.py"])
            repo.index.commit("Initial")

            test_file.write_text("modified")

            watcher = IbexWatcher(temp_dir)

            # Detect changes twice
            count1 = watcher.detect_current_changes()
            count2 = watcher.detect_current_changes()

            # Should only have one change entry
            state = watcher.load_state()
            assert len(state['changes']) == 1


class TestStakeCreation:
    """Test stake creation functionality"""

    @pytest.mark.asyncio
    async def test_create_stake_with_no_changes(self):
        """Test creating stake when no changes exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir)

            # Mock to avoid actual LLM calls
            watcher.llm.analyze_changes = AsyncMock(return_value="Analysis")

            await watcher.create_stake("test-stake", "Test message", auto_detect=False)

            # Should not create stake
            state = watcher.load_state()
            assert len(state['stakes']) == 0

    @pytest.mark.asyncio
    async def test_create_stake_with_auto_detect(self):
        """Test stake creation with auto-detect enabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup git repo with changes
            repo = Repo.init(temp_dir)
            repo.config_writer().set_value("user", "name", "Test").release()
            repo.config_writer().set_value("user", "email", "test@test.com").release()

            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("original")
            repo.index.add(["test.py"])
            repo.index.commit("Initial")

            test_file.write_text("modified")

            watcher = IbexWatcher(temp_dir)

            # Mock LLM and git operations
            watcher.llm.analyze_changes = AsyncMock(return_value="LLM Analysis")
            watcher.llm.store_semantic_change = Mock()
            watcher.git.stage_all_changes = Mock()
            watcher.git.commit = Mock(return_value=Mock(hexsha="abc123"))

            await watcher.create_stake("test-stake", "Test message", auto_detect=True)

            # Should detect changes and create stake
            state = watcher.load_state()
            assert len(state['stakes']) == 1
            assert state['stakes'][0]['name'] == "test-stake"

    @pytest.mark.asyncio
    async def test_create_stake_clears_changes(self):
        """Test that creating stake clears changes from state"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir)

            # Add some changes
            state = watcher.load_state()
            state['changes'] = [{'file': 'test.py', 'hash': 'abc'}]
            watcher.save_state(state)

            # Mock operations
            watcher.llm.analyze_changes = AsyncMock(return_value="Analysis")
            watcher.llm.store_semantic_change = Mock()
            watcher.git.stage_all_changes = Mock()
            watcher.git.commit = Mock(return_value=Mock(hexsha="abc123"))

            await watcher.create_stake("stake1", "Message")

            # Changes should be cleared
            state = watcher.load_state()
            assert len(state['changes']) == 0

    @pytest.mark.asyncio
    async def test_create_stake_stores_semantic_info(self):
        """Test that stake creation stores semantic information"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir, intent="Test intent")

            # Add changes
            state = watcher.load_state()
            state['changes'] = [{'file': 'test.py', 'hash': 'abc'}]
            watcher.save_state(state)

            # Mock operations
            llm_analysis = "Detailed LLM analysis"
            watcher.llm.analyze_changes = AsyncMock(return_value=llm_analysis)
            watcher.llm.store_semantic_change = Mock()
            watcher.git.stage_all_changes = Mock()

            commit_hash = "abc123def456"
            watcher.git.commit = Mock(return_value=Mock(hexsha=commit_hash))

            await watcher.create_stake("stake1", "User message")

            # Verify semantic information was stored
            watcher.llm.store_semantic_change.assert_called_once()
            call_args = watcher.llm.store_semantic_change.call_args[0]

            assert call_args[0] == commit_hash
            assert call_args[1] == llm_analysis
            assert len(call_args[2]) == 1  # changes
            assert call_args[3] == "Test intent"


class TestEventHandler:
    """Test IbexEventHandler"""

    def test_event_handler_initialization(self):
        """Test event handler initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir)
            handler = IbexEventHandler(watcher)

            assert handler.watcher == watcher

    def test_event_handler_ignores_directories(self):
        """Test that handler ignores directory events"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir)
            handler = IbexEventHandler(watcher)

            # Create a mock event for directory
            event = Mock()
            event.is_directory = True
            event.src_path = str(Path(temp_dir) / "subdir")

            # Mock handle_change to track calls
            watcher.handle_change = Mock()

            handler.on_modified(event)

            # Should not call handle_change for directories
            watcher.handle_change.assert_not_called()

    def test_event_handler_ignores_ibex_directory(self):
        """Test that handler ignores .ibex directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir)
            handler = IbexEventHandler(watcher)

            event = Mock()
            event.is_directory = False
            event.src_path = str(Path(temp_dir) / ".ibex" / "state.json")

            watcher.handle_change = Mock()

            handler.on_modified(event)

            # Should not call handle_change for .ibex files
            watcher.handle_change.assert_not_called()

    def test_event_handler_processes_regular_files(self):
        """Test that handler processes regular file changes"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir)
            handler = IbexEventHandler(watcher)

            event = Mock()
            event.is_directory = False
            event.src_path = str(Path(temp_dir) / "test.py")

            watcher.handle_change = Mock()

            handler.on_modified(event)

            # Should call handle_change
            watcher.handle_change.assert_called_once_with(event.src_path)


class TestObserverManagement:
    """Test file observer start/stop functionality"""

    def test_start_observer(self):
        """Test starting the file observer"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir)

            watcher.start()

            # Observer should be alive
            assert watcher.observer.is_alive()

            watcher.stop()

    def test_stop_observer(self):
        """Test stopping the file observer"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir)

            watcher.start()
            assert watcher.observer.is_alive()

            watcher.stop()

            # Observer should be stopped
            assert not watcher.observer.is_alive()

    def test_stop_observer_when_not_running(self):
        """Test that stopping observer when not running doesn't error"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir)

            # Should not raise exception
            watcher.stop()


class TestErrorHandling:
    """Test error handling in core functionality"""

    def test_handle_change_with_missing_file(self):
        """Test handling change when file doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir)

            # Try to handle nonexistent file - should not crash
            watcher.handle_change("/nonexistent/file.py")

            # State should remain valid
            state = watcher.load_state()
            assert isinstance(state, dict)

    def test_handle_change_with_binary_file(self):
        """Test handling change for binary file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            watcher = IbexWatcher(temp_dir)

            # Create binary file
            binary_file = Path(temp_dir) / "image.png"
            binary_file.write_bytes(b'\x89PNG\r\n\x1a\n')

            # Mock git to track it
            watcher.git.get_uncommitted_changes = Mock(return_value=[str(binary_file)])

            # Should handle gracefully
            watcher.handle_change(str(binary_file))

            state = watcher.load_state()
            # Should still record the change with special hash
            if len(state['changes']) > 0:
                assert state['changes'][0]['hash'] == 'binary'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
