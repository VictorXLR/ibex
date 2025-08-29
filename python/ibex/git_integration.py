from git import Repo, GitCommandError
from pathlib import Path
from typing import Optional, List

class GitManager:
    def __init__(self, path: str):
        self.path = Path(path)
        try:
            self.repo = Repo(path)
        except:
            self.repo = Repo.init(path)
    
    def stage_changes(self, files: Optional[List[str]] = None):
        """Stage specific files or all changes"""
        if files:
            self.repo.index.add(files)
        else:
            self.repo.git.add(A=True)
    
    def commit(self, message: str, description: str = ""):
        """Create a commit with the given message and optional description"""
        try:
            if description:
                full_message = f"{message}\n\n{description}"
            else:
                full_message = message

            commit_obj = self.repo.index.commit(full_message)
            return commit_obj
        except GitCommandError as e:
            print(f"Git commit error: {e}")
            return None
    
    def get_uncommitted_changes(self) -> List[str]:
        """Get list of files with uncommitted changes (including untracked files)"""
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

        return unique_changes
