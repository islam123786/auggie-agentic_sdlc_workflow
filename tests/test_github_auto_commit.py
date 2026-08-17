#!/usr/bin/env python3
"""
Test script to verify GitHub auto-commit implementation
"""
import sys
import os
import tempfile
import subprocess
from pathlib import Path

# Add orchestrator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orchestrator.config import Config
from orchestrator.workflow_engine import WorkflowEngine


def test_config_github_settings():
    """Test that Config has GitHub settings"""
    print("=" * 70)
    print("TEST 1: Config GitHub Settings")
    print("=" * 70)
    
    config = Config()
    
    # Check all GitHub attributes exist
    assert hasattr(config, 'github_enabled'), "github_enabled attribute missing"
    assert hasattr(config, 'github_auto_commit'), "github_auto_commit attribute missing"
    assert hasattr(config, 'github_repository_url'), "github_repository_url attribute missing"
    assert hasattr(config, 'github_branch'), "github_branch attribute missing"
    assert hasattr(config, 'github_commit_message_prefix'), "github_commit_message_prefix attribute missing"
    assert hasattr(config, 'github_user_name'), "github_user_name attribute missing"
    assert hasattr(config, 'github_user_email'), "github_user_email attribute missing"
    
    print(f"✓ github_enabled: {config.github_enabled}")
    print(f"✓ github_auto_commit: {config.github_auto_commit}")
    print(f"✓ github_repository_url: {config.github_repository_url}")
    print(f"✓ github_branch: {config.github_branch}")
    print(f"✓ github_commit_message_prefix: {config.github_commit_message_prefix}")
    print(f"✓ github_user_name: {config.github_user_name}")
    print(f"✓ github_user_email: {config.github_user_email}")
    
    # Check default values
    assert config.github_enabled == False, "github_enabled should default to False"
    assert config.github_auto_commit == False, "github_auto_commit should default to False"
    assert config.github_branch == "main", "github_branch should default to 'main'"
    
    print("\n✅ All Config GitHub settings present with correct defaults!\n")
    return True


def test_workflow_engine_git_method():
    """Test that WorkflowEngine has git commit method"""
    print("=" * 70)
    print("TEST 2: WorkflowEngine Git Method")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        config.workspace_root = tmpdir
        config.state_db_path = os.path.join(tmpdir, '.state.db')
        
        engine = WorkflowEngine(config)
        
        # Check method exists
        assert hasattr(engine, '_git_commit_task'), "_git_commit_task method missing"
        print("✓ _git_commit_task method exists")
        
        # Check method signature
        import inspect
        sig = inspect.signature(engine._git_commit_task)
        params = sig.parameters
        
        assert 'task_id' in params, "task_id parameter missing"
        assert 'task_title' in params, "task_title parameter missing"
        print("✓ _git_commit_task has correct parameters: task_id, task_title")
        
        # Check project_code_dir is set
        assert hasattr(engine, 'project_code_dir'), "project_code_dir attribute missing"
        expected_path = Path(tmpdir) / 'project-code'
        assert engine.project_code_dir == expected_path, f"project_code_dir incorrect: {engine.project_code_dir}"
        print(f"✓ project_code_dir set correctly: {engine.project_code_dir}")
        
        print("\n✅ WorkflowEngine git method test passed!\n")
        return True


def test_git_helper_script_exists():
    """Test that git helper script exists and has required functions"""
    print("=" * 70)
    print("TEST 3: Git Helper Script")
    print("=" * 70)
    
    script_path = Path(__file__).parent.parent / "agents" / "common" / "git_helper.sh"
    
    assert script_path.exists(), f"Git helper script not found: {script_path}"
    print(f"✓ Git helper script exists: {script_path}")
    
    # Read script content
    content = script_path.read_text()
    
    # Check for required functions
    required_functions = [
        'git_init_if_needed',
        'git_configure_user',
        'git_add_remote',
        'git_commit_changes',
        'git_push_changes',
        'git_commit_and_push'
    ]
    
    for func in required_functions:
        assert func in content, f"Function {func} not found in git_helper.sh"
        print(f"✓ Function exists: {func}")
    
    print("\n✅ Git helper script test passed!\n")
    return True


def test_config_yaml_github_section():
    """Test that config.yaml has GitHub section"""
    print("=" * 70)
    print("TEST 4: config.yaml GitHub Section")
    print("=" * 70)
    
    config_path = Path(__file__).parent.parent / "config.yaml"
    
    assert config_path.exists(), "config.yaml not found"
    print(f"✓ config.yaml exists: {config_path}")
    
    # Read config content
    content = config_path.read_text()
    
    # Check for GitHub section
    assert 'github:' in content, "github: section not found in config.yaml"
    print("✓ github: section exists in config.yaml")
    
    # Check for key settings
    assert 'enabled:' in content, "enabled setting missing"
    assert 'auto_commit:' in content, "auto_commit setting missing"
    assert 'repository_url:' in content, "repository_url setting missing"
    assert 'branch:' in content, "branch setting missing"
    assert 'commit_message_prefix:' in content, "commit_message_prefix setting missing"
    
    print("✓ All required GitHub settings present in config.yaml")
    
    print("\n✅ config.yaml test passed!\n")
    return True


def test_cli_github_flags():
    """Test that CLI has GitHub flags"""
    print("=" * 70)
    print("TEST 5: CLI GitHub Flags")
    print("=" * 70)
    
    try:
        from orchestrator.cli import cli
        
        # Check run command
        run_cmd = cli.commands['run']
        run_params = {p.name for p in run_cmd.params}
        
        assert 'github_enable' in run_params, "github_enable flag missing from run command"
        assert 'github_push' in run_params, "github_push flag missing from run command"
        assert 'github_repo' in run_params, "github_repo flag missing from run command"
        assert 'github_branch' in run_params, "github_branch flag missing from run command"
        
        print("✓ run command has all GitHub flags:")
        print("  • --github-enable")
        print("  • --github-push")
        print("  • --github-repo")
        print("  • --github-branch")
        
        # Check resume command
        resume_cmd = cli.commands['resume']
        resume_params = {p.name for p in resume_cmd.params}
        
        assert 'github_enable' in resume_params, "github_enable flag missing from resume command"
        assert 'github_push' in resume_params, "github_push flag missing from resume command"
        assert 'github_repo' in resume_params, "github_repo flag missing from resume command"
        
        print("✓ resume command has GitHub flags")
        
        print("\n✅ CLI GitHub flags test passed!\n")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("GITHUB AUTO-COMMIT - IMPLEMENTATION VERIFICATION")
    print("=" * 70 + "\n")
    
    results = []
    
    # Run all tests
    results.append(("Config GitHub Settings", test_config_github_settings()))
    results.append(("WorkflowEngine Git Method", test_workflow_engine_git_method()))
    results.append(("Git Helper Script", test_git_helper_script_exists()))
    results.append(("config.yaml GitHub Section", test_config_yaml_github_section()))
    results.append(("CLI GitHub Flags", test_cli_github_flags()))
    
    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<40} {status}")
    
    print("=" * 70)
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n🎉 ALL TESTS PASSED - GitHub auto-commit is properly implemented!\n")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - Please review the implementation\n")
        sys.exit(1)
