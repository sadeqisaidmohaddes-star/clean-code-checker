"""Clean Code Checker — analyse a GitHub repository for clean-code issues.

The public entry point is :func:`cleancode.analyzer.analyze_repo`.
"""

from .analyzer import analyze_repo
from .github import GitHubError

__all__ = ["analyze_repo", "GitHubError"]
__version__ = "1.0.0"
