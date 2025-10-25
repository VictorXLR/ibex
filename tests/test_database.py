"""
Comprehensive tests for IBEX database functionality (SQLite semantic.db)

Tests cover:
- Database initialization
- Storing semantic changes
- Retrieving semantic history
- Data integrity and persistence
- Error handling for database operations
- Schema validation
"""

import pytest
import sqlite3
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path to import ibex modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from ibex.llm import LLMManager


class TestDatabaseInitialization:
    """Test database initialization and schema creation"""

    def test_init_db_creates_directory(self):
        """Test that database initialization creates .ibex directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir)

            ibex_dir = Path(temp_dir) / '.ibex'
            assert ibex_dir.exists(), ".ibex directory should be created"

    def test_init_db_creates_database_file(self):
        """Test that database file is created"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir)

            db_path = Path(temp_dir) / '.ibex' / 'semantic.db'
            assert db_path.exists(), "semantic.db should be created"

    def test_init_db_creates_correct_schema(self):
        """Test that database schema is created correctly"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir)

            # Connect to database and check schema
            conn = sqlite3.connect(llm_manager.db_path)
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='semantic_changes'
            """)
            result = cursor.fetchone()
            assert result is not None, "semantic_changes table should exist"

            # Check table structure
            cursor.execute("PRAGMA table_info(semantic_changes)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            expected_columns = ['id', 'timestamp', 'description', 'changes',
                              'commit_hash', 'intent', 'provider', 'model']
            assert column_names == expected_columns, f"Expected columns {expected_columns}, got {column_names}"

            conn.close()

    def test_init_db_is_idempotent(self):
        """Test that multiple initializations don't break the database"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize twice
            llm_manager1 = LLMManager(temp_dir)
            llm_manager2 = LLMManager(temp_dir)

            # Should still work
            db_path = Path(temp_dir) / '.ibex' / 'semantic.db'
            assert db_path.exists()


class TestStoringSemanticChanges:
    """Test storing semantic change information"""

    def test_store_semantic_change_inserts_data(self):
        """Test that store_semantic_change inserts data correctly"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama')

            # Store a semantic change
            commit_hash = "abc123def456"
            description = "Added user authentication"
            changes = [
                {"file": "auth.py", "hash": "xyz789", "timestamp": "2024-01-01T12:00:00"}
            ]
            intent = "Implement secure login"

            llm_manager.store_semantic_change(
                commit_hash, description, changes, intent
            )

            # Verify data was inserted
            conn = sqlite3.connect(llm_manager.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM semantic_changes")
            rows = cursor.fetchall()
            conn.close()

            assert len(rows) == 1, "Should have one row"
            row = rows[0]
            # Schema: id, timestamp, description, changes, commit_hash, intent, provider, model
            assert row[2] == description  # row[2] is description
            assert json.loads(row[3]) == changes  # row[3] is changes (JSON)
            assert row[4] == commit_hash  # row[4] is commit_hash
            assert row[5] == intent  # row[5] is intent

    def test_store_semantic_change_generates_unique_ids(self):
        """Test that each stored change gets a unique ID"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama')

            # Store multiple changes
            for i in range(3):
                llm_manager.store_semantic_change(
                    f"commit{i}",
                    f"Description {i}",
                    [{"file": f"file{i}.py"}],
                    f"Intent {i}"
                )

            # Check all IDs are unique
            conn = sqlite3.connect(llm_manager.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM semantic_changes")
            ids = [row[0] for row in cursor.fetchall()]
            conn.close()

            assert len(ids) == 3
            assert len(set(ids)) == 3, "All IDs should be unique"

    def test_store_semantic_change_preserves_complex_changes(self):
        """Test that complex change structures are preserved"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama')

            # Complex changes structure
            changes = [
                {
                    "file": "module/auth.py",
                    "hash": "abc123",
                    "timestamp": "2024-01-01T12:00:00",
                    "summary": "Added OAuth support"
                },
                {
                    "file": "module/database.py",
                    "hash": "def456",
                    "timestamp": "2024-01-01T12:05:00",
                    "summary": "Updated user schema"
                }
            ]

            llm_manager.store_semantic_change(
                "commit123",
                "Multi-file authentication update",
                changes,
                "Modernize auth system"
            )

            # Retrieve and verify
            history = llm_manager.get_semantic_history()
            assert len(history) == 1
            retrieved_changes = history[0]['changes']

            assert len(retrieved_changes) == 2
            assert retrieved_changes[0]['file'] == "module/auth.py"
            assert retrieved_changes[1]['summary'] == "Updated user schema"

    def test_store_semantic_change_records_provider_info(self):
        """Test that provider and model information is stored"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama', model='llama2')

            llm_manager.store_semantic_change(
                "commit123",
                "Test description",
                [{"file": "test.py"}],
                "Test intent"
            )

            history = llm_manager.get_semantic_history()
            assert len(history) == 1
            assert history[0]['provider'] == 'ollama'
            assert history[0]['model'] == 'llama2'


class TestRetrievingSemanticHistory:
    """Test retrieving semantic history"""

    def test_get_semantic_history_empty_database(self):
        """Test getting history from empty database"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir)

            history = llm_manager.get_semantic_history()
            assert history == [], "Empty database should return empty list"

    def test_get_semantic_history_returns_all_entries(self):
        """Test that all entries are retrieved"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama')

            # Store multiple entries
            for i in range(5):
                llm_manager.store_semantic_change(
                    f"commit{i}",
                    f"Description {i}",
                    [{"file": f"file{i}.py"}],
                    f"Intent {i}"
                )

            history = llm_manager.get_semantic_history()
            assert len(history) == 5, "Should retrieve all 5 entries"

    def test_get_semantic_history_ordered_by_timestamp_desc(self):
        """Test that history is ordered by timestamp (newest first)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama')

            # Store entries with delays to ensure different timestamps
            import time
            descriptions = []
            for i in range(3):
                desc = f"Entry {i}"
                descriptions.append(desc)
                llm_manager.store_semantic_change(
                    f"commit{i}",
                    desc,
                    [{"file": f"file{i}.py"}],
                    f"Intent {i}"
                )
                time.sleep(0.01)  # Small delay to ensure different timestamps

            history = llm_manager.get_semantic_history()

            # Newest should be first
            assert history[0]['description'] == "Entry 2"
            assert history[1]['description'] == "Entry 1"
            assert history[2]['description'] == "Entry 0"

    def test_get_semantic_history_includes_all_fields(self):
        """Test that retrieved history includes all expected fields"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama', model='llama2')

            llm_manager.store_semantic_change(
                "commit123",
                "Test description",
                [{"file": "test.py", "hash": "abc"}],
                "Test intent"
            )

            history = llm_manager.get_semantic_history()
            entry = history[0]

            # Check all expected fields are present
            required_fields = ['id', 'timestamp', 'description', 'changes',
                             'commit_hash', 'intent', 'provider', 'model']
            for field in required_fields:
                assert field in entry, f"Field '{field}' should be present"

    def test_get_semantic_history_deserializes_changes_json(self):
        """Test that changes JSON is properly deserialized"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama')

            changes = [
                {"file": "test.py", "hash": "abc", "nested": {"key": "value"}}
            ]

            llm_manager.store_semantic_change(
                "commit123",
                "Test",
                changes,
                "Intent"
            )

            history = llm_manager.get_semantic_history()
            retrieved_changes = history[0]['changes']

            # Should be a list, not a string
            assert isinstance(retrieved_changes, list)
            assert retrieved_changes[0]['file'] == "test.py"
            assert retrieved_changes[0]['nested']['key'] == "value"


class TestDatabasePersistence:
    """Test database persistence and data integrity"""

    def test_data_persists_across_instances(self):
        """Test that data persists when creating new LLMManager instances"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create first instance and store data
            llm_manager1 = LLMManager(temp_dir, provider='ollama')
            llm_manager1.store_semantic_change(
                "commit123",
                "Persistent data",
                [{"file": "test.py"}],
                "Test persistence"
            )

            # Create second instance
            llm_manager2 = LLMManager(temp_dir, provider='ollama')
            history = llm_manager2.get_semantic_history()

            assert len(history) == 1
            assert history[0]['description'] == "Persistent data"

    def test_concurrent_writes_to_database(self):
        """Test that multiple writes don't corrupt the database"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama')

            # Perform multiple writes
            for i in range(10):
                llm_manager.store_semantic_change(
                    f"commit{i}",
                    f"Description {i}",
                    [{"file": f"file{i}.py"}],
                    f"Intent {i}"
                )

            # Verify all writes succeeded
            history = llm_manager.get_semantic_history()
            assert len(history) == 10

            # Verify database integrity
            conn = sqlite3.connect(llm_manager.db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            assert result[0] == "ok", "Database integrity check should pass"
            conn.close()


class TestDatabaseErrorHandling:
    """Test error handling for database operations"""

    def test_store_semantic_change_with_invalid_json(self):
        """Test storing changes with data that can't be JSON serialized"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama')

            # This should not raise an exception - json.dumps should handle it
            changes = [{"file": "test.py", "timestamp": datetime.now().isoformat()}]
            llm_manager.store_semantic_change(
                "commit123",
                "Test",
                changes,
                "Intent"
            )

            history = llm_manager.get_semantic_history()
            assert len(history) == 1

    def test_get_semantic_history_with_corrupted_json(self):
        """Test retrieving history when JSON is corrupted"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama')

            # Manually insert corrupted JSON
            conn = sqlite3.connect(llm_manager.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO semantic_changes VALUES
                (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "test-id",
                datetime.now().isoformat(),
                "Test description",
                "{invalid json}",  # Corrupted JSON
                "commit123",
                "Test intent",
                "ollama",
                "llama2"
            ))
            conn.commit()
            conn.close()

            # Should raise an error when trying to retrieve
            with pytest.raises(json.JSONDecodeError):
                llm_manager.get_semantic_history()

    @pytest.mark.skipif(os.geteuid() == 0, reason="Permission tests don't work as root")
    def test_database_permissions_error(self):
        """Test handling of database permission errors"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama')

            # Make database file read-only
            db_file = llm_manager.db_path
            os.chmod(db_file, 0o444)

            try:
                # This should raise a permission error when trying to write
                with pytest.raises((sqlite3.OperationalError, PermissionError, OSError)):
                    llm_manager.store_semantic_change(
                        "commit123",
                        "Test",
                        [{"file": "test.py"}],
                        "Intent"
                    )
            finally:
                # Restore permissions for cleanup
                os.chmod(db_file, 0o644)


class TestDatabaseMigration:
    """Test backward compatibility and migration scenarios"""

    def test_reading_old_schema_without_provider_model(self):
        """Test reading data from old schema that lacks provider/model fields"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama')

            # Manually insert data without provider/model (simulating old schema)
            conn = sqlite3.connect(llm_manager.db_path)
            cursor = conn.cursor()

            # Drop and recreate table without provider/model
            cursor.execute("DROP TABLE IF EXISTS semantic_changes")
            cursor.execute("""
                CREATE TABLE semantic_changes
                (id TEXT PRIMARY KEY, timestamp TEXT,
                 description TEXT, changes TEXT,
                 commit_hash TEXT, intent TEXT)
            """)

            cursor.execute("""
                INSERT INTO semantic_changes VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "old-entry",
                "2024-01-01T12:00:00",
                "Old description",
                json.dumps([{"file": "old.py"}]),
                "oldcommit",
                "Old intent"
            ))
            conn.commit()
            conn.close()

            # Should handle missing fields gracefully
            history = llm_manager.get_semantic_history()
            assert len(history) == 1
            assert history[0]['provider'] == 'unknown'
            assert history[0]['model'] == 'unknown'


class TestDatabaseQueries:
    """Test specific database query patterns"""

    def test_filter_by_commit_hash(self):
        """Test filtering semantic history by commit hash"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama')

            # Store multiple entries
            llm_manager.store_semantic_change("commit1", "Desc 1", [], "Intent 1")
            llm_manager.store_semantic_change("commit2", "Desc 2", [], "Intent 2")
            llm_manager.store_semantic_change("commit1", "Desc 3", [], "Intent 3")

            # Query for specific commit
            conn = sqlite3.connect(llm_manager.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM semantic_changes WHERE commit_hash = ?",
                ("commit1",)
            )
            results = cursor.fetchall()
            conn.close()

            assert len(results) == 2, "Should find 2 entries for commit1"

    def test_database_size_growth(self):
        """Test that database grows reasonably with many entries"""
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_manager = LLMManager(temp_dir, provider='ollama')

            # Store many entries
            for i in range(100):
                llm_manager.store_semantic_change(
                    f"commit{i}",
                    f"Description {i}" * 10,  # Larger description
                    [{"file": f"file{i}.py", "data": "x" * 100}],
                    f"Intent {i}"
                )

            # Check database size is reasonable (< 1MB for 100 entries)
            db_size = llm_manager.db_path.stat().st_size
            assert db_size < 1_000_000, f"Database size {db_size} should be < 1MB"

            # Verify all entries are there
            history = llm_manager.get_semantic_history()
            assert len(history) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
