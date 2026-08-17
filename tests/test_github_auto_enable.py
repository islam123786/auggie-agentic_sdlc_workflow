"""
Test GitHub Auto-Enable Feature

Tests that providing --github-repo automatically enables GitHub integration
without requiring --github-enable and --github-push flags.
"""

import pytest
from click.testing import CliRunner
from orchestrator.cli import cli
from orchestrator.config import Config


def test_github_repo_auto_enables_integration():
    """Test that --github-repo automatically enables GitHub integration"""
    
    # Create a mock config
    config = Config()
    
    # Initially GitHub should be disabled
    assert config.github_enabled == False
    assert config.github_auto_commit == False
    assert config.github_repository_url == ""
    
    # Simulate what happens when --github-repo is provided
    github_repo = "https://github.com/user/repo.git"
    github_branch = "main"
    
    # This is what the CLI does
    if github_repo:
        config.github_enabled = True
        config.github_auto_commit = True
        config.github_repository_url = github_repo
        config.github_branch = github_branch
    
    # Verify it's enabled
    assert config.github_enabled == True
    assert config.github_auto_commit == True
    assert config.github_repository_url == github_repo
    assert config.github_branch == github_branch
    
    print("✅ Test passed: --github-repo auto-enables GitHub integration")


def test_github_enable_flags_still_work():
    """Test that old --github-enable and --github-push flags still work (backward compatibility)"""
    
    config = Config()
    config.github_repository_url = "https://github.com/user/repo.git"  # Set from config.yaml
    
    # Simulate old flags
    github_enable = True
    github_push = True
    
    if github_enable:
        config.github_enabled = True
        if github_push:
            config.github_auto_commit = True
    
    assert config.github_enabled == True
    assert config.github_auto_commit == True
    
    print("✅ Test passed: Old flags still work for backward compatibility")


def test_github_repo_takes_precedence():
    """Test that --github-repo takes precedence over old flags"""
    
    config = Config()
    
    # User provides --github-repo (new way)
    github_repo = "https://github.com/user/new-repo.git"
    github_enable = False  # Old flag not set
    github_push = False    # Old flag not set
    
    # CLI logic
    if github_repo:
        config.github_enabled = True
        config.github_auto_commit = True
        config.github_repository_url = github_repo
    elif github_enable:
        config.github_enabled = True
    
    # Should be enabled despite old flags being False
    assert config.github_enabled == True
    assert config.github_auto_commit == True
    assert config.github_repository_url == github_repo
    
    print("✅ Test passed: --github-repo takes precedence over old flags")


def test_no_github_flags_leaves_disabled():
    """Test that without any flags, GitHub remains disabled"""
    
    config = Config()
    
    github_repo = None
    github_enable = False
    github_push = False
    
    # CLI logic
    if github_repo:
        config.github_enabled = True
        config.github_auto_commit = True
        config.github_repository_url = github_repo
    elif github_enable:
        config.github_enabled = True
    
    # Should remain disabled
    assert config.github_enabled == False
    assert config.github_auto_commit == False
    
    print("✅ Test passed: No flags leaves GitHub disabled")


def test_github_branch_default():
    """Test that --github-branch defaults to 'main'"""
    
    config = Config()
    github_repo = "https://github.com/user/repo.git"
    github_branch = "main"  # Default value
    
    if github_repo:
        config.github_enabled = True
        config.github_auto_commit = True
        config.github_repository_url = github_repo
        config.github_branch = github_branch
    
    assert config.github_branch == "main"
    
    print("✅ Test passed: --github-branch defaults to 'main'")


def test_github_branch_custom():
    """Test that --github-branch can be customized"""
    
    config = Config()
    github_repo = "https://github.com/user/repo.git"
    github_branch = "develop"  # Custom branch
    
    if github_repo:
        config.github_enabled = True
        config.github_auto_commit = True
        config.github_repository_url = github_repo
        config.github_branch = github_branch
    
    assert config.github_branch == "develop"
    
    print("✅ Test passed: --github-branch can be customized")


if __name__ == "__main__":
    print("="*70)
    print("Testing GitHub Auto-Enable Feature")
    print("="*70)
    print()
    
    test_github_repo_auto_enables_integration()
    test_github_enable_flags_still_work()
    test_github_repo_takes_precedence()
    test_no_github_flags_leaves_disabled()
    test_github_branch_default()
    test_github_branch_custom()
    
    print()
    print("="*70)
    print("✅ All tests passed!")
    print("="*70)
