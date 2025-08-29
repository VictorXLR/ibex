from git import Repo, GitCommandError
from pathlib import Path
from typing import Optional, List
from functools import lru_cache
from datetime import datetime

class GitManager:
    def __init__(self, path: str):
        self.path = Path(path)
        try:
            self.repo = Repo(path)
        except:
            self.repo = Repo.init(path)

        # LRU Cache configuration
        self._uncommitted_cache = None
        self._cache_timestamp = None
        self._cache_max_age = 10  # seconds for git operations

    def _is_cache_expired(self) -> bool:
        """Check if git cache has expired"""
        if self._cache_timestamp is None:
            return True
        return (datetime.now() - self._cache_timestamp).seconds > self._cache_max_age

    def _invalidate_git_cache(self):
        """Invalidate the git status cache"""
        self._uncommitted_cache = None
        self._cache_timestamp = None

    def stage_changes(self, files: Optional[List[str]] = None):
        """Stage specific files or all changes"""
        if files:
            self.repo.index.add(files)
        else:
            self.repo.git.add(A=True)

        # Invalidate cache after staging
        self._invalidate_git_cache()

    def stage_all_changes(self):
        """Stage all changes including untracked files"""
        self.repo.git.add(A=True)

        # Invalidate cache after staging
        self._invalidate_git_cache()
    
    def commit(self, message: str, description: str = ""):
        """Create a commit with the given message and optional description"""
        try:
            if description:
                full_message = f"{message}\n\n{description}"
            else:
                full_message = message

            commit_obj = self.repo.index.commit(full_message)

            # Invalidate cache after commit
            self._invalidate_git_cache()

            return commit_obj
        except GitCommandError as e:
            print(f"Git commit error: {e}")
            return None
    
    def get_uncommitted_changes(self) -> List[str]:
        """Get list of files with uncommitted changes (including untracked files) with caching"""
        # Check cache first
        if self._uncommitted_cache is not None and not self._is_cache_expired():
            return self._uncommitted_cache.copy()

        changes = []

        # Get staged changes
        try:
            changes.extend([item.a_path for item in self.repo.index.diff(None)])
        except:
            pass

        # Get unstaged changes
        try:
            changes.extend([item.a_path for item in self.repo.index.diff('HEAD')])
        except:
            pass

        # Get untracked files
        try:
            untracked = self.repo.untracked_files
            changes.extend(untracked)
        except:
            pass

        # Remove duplicates while preserving order
        seen = set()
        unique_changes = []
        for change in changes:
            if change not in seen:
                seen.add(change)
                unique_changes.append(change)

        # Cache the result
        self._uncommitted_cache = unique_changes.copy()
        self._cache_timestamp = datetime.now()

        return unique_changes
