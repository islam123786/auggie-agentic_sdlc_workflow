#!/usr/bin/env python3
"""
Test script to verify resume capability implementation
"""
import sys
import os
import tempfile
import sqlite3
from pathlib import Path

# Add orchestrator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orchestrator.state_manager import StateManager
from orchestrator.config import Config
from orchestrator.workflow_engine import WorkflowEngine


def test_state_manager_resume_methods():
    """Test StateManager resume-related methods"""
    print("=" * 70)
    print("TEST 1: StateManager Resume Methods")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, '.state.db')
        state = StateManager(db_path)
        
        # Create a workflow
        workflow_id = state.create_workflow('/fake/requirements.md')
        print(f"✓ Created workflow: {workflow_id}")
        
        # Add some phases
        state.update_phase(workflow_id, "architecture", {"status": "completed"})
        state.update_phase(workflow_id, "task_planning", {"status": "completed"})
        state.update_phase(workflow_id, "setup", {"status": "completed"})
        print("✓ Added completed phases: architecture, task_planning, setup")
        
        # Add some tasks
        state.update_task(workflow_id, "task-001", "completed")
        state.update_task(workflow_id, "task-002", "completed")
        state.update_task(workflow_id, "task-003", "running")
        print("✓ Added tasks: task-001 (completed), task-002 (completed), task-003 (running)")
        
        # Mark workflow as failed
        state.mark_failed(workflow_id, "Test failure")
        print("✓ Marked workflow as failed")
        
        # Test get_last_completed_phase
        last_phase = state.get_last_completed_phase(workflow_id)
        assert last_phase == "setup", f"Expected 'setup', got '{last_phase}'"
        print(f"✓ get_last_completed_phase() returned: {last_phase}")
        
        # Test get_completed_tasks
        completed_tasks = state.get_completed_tasks(workflow_id)
        assert len(completed_tasks) == 2, f"Expected 2 tasks, got {len(completed_tasks)}"
        assert "task-001" in completed_tasks, "task-001 not in completed tasks"
        assert "task-002" in completed_tasks, "task-002 not in completed tasks"
        print(f"✓ get_completed_tasks() returned: {completed_tasks}")
        
        # Test resume_workflow
        state.resume_workflow(workflow_id)
        workflow = state.get_workflow(workflow_id)
        assert workflow['status'] == 'running', f"Expected 'running', got '{workflow['status']}'"
        print(f"✓ resume_workflow() changed status to: {workflow['status']}")
        
        # Test resume on non-failed workflow (should raise error)
        try:
            state.resume_workflow(workflow_id)
            print("✗ resume_workflow() should have raised ValueError for running workflow")
            return False
        except ValueError as e:
            print(f"✓ resume_workflow() correctly raised ValueError: {e}")
        
        print("\n✅ All StateManager tests passed!\n")
        return True


def test_workflow_engine_resume_flag():
    """Test WorkflowEngine resume parameter handling"""
    print("=" * 70)
    print("TEST 2: WorkflowEngine Resume Parameter")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create config
        config = Config()
        config.workspace_root = tmpdir
        config.state_db_path = os.path.join(tmpdir, '.state.db')
        
        # Create engine
        engine = WorkflowEngine(config)
        print(f"✓ Created WorkflowEngine with workspace: {tmpdir}")
        
        # Test that run_workflow accepts resume parameter
        try:
            # This will fail because we don't have actual agents, but we can check the signature
            import inspect
            sig = inspect.signature(engine.run_workflow)
            params = sig.parameters
            
            assert 'resume' in params, "'resume' parameter not found"
            assert params['resume'].default == False, "resume parameter should default to False"
            print("✓ run_workflow() has 'resume' parameter with default=False")
            
            print("\n✅ WorkflowEngine parameter test passed!\n")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            return False


def test_cli_commands_exist():
    """Test that CLI commands are properly registered"""
    print("=" * 70)
    print("TEST 3: CLI Commands")
    print("=" * 70)
    
    try:
        from orchestrator.cli import cli
        
        # Get all commands
        commands = cli.commands
        
        # Check for resume command
        assert 'resume' in commands, "resume command not found"
        print("✓ 'resume' command exists")
        
        # Check for enhanced status command
        assert 'status' in commands, "status command not found"
        print("✓ 'status' command exists")
        
        # Check for enhanced list command
        assert 'list' in commands, "list command not found"
        print("✓ 'list' command exists")
        
        # Check resume command parameters
        resume_cmd = commands['resume']
        resume_params = {p.name for p in resume_cmd.params}
        assert 'workflow_id' in resume_params, "workflow_id parameter missing from resume"
        assert 'workspace' in resume_params, "workspace parameter missing from resume"
        print("✓ resume command has required parameters: workflow_id, workspace")
        
        print("\n✅ All CLI tests passed!\n")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_schema():
    """Test that database schema supports resume queries"""
    print("=" * 70)
    print("TEST 4: Database Schema")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, '.state.db')
        state = StateManager(db_path)
        
        # Check tables exist
        with state._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            
            assert 'workflows' in tables, "workflows table not found"
            assert 'phases' in tables, "phases table not found"
            assert 'tasks' in tables, "tasks table not found"
            print(f"✓ All required tables exist: {tables}")
            
            # Check workflows table has status column
            cursor.execute("PRAGMA table_info(workflows)")
            workflow_cols = {row[1] for row in cursor.fetchall()}
            assert 'status' in workflow_cols, "status column missing from workflows"
            print(f"✓ workflows table columns: {workflow_cols}")
            
            # Check phases table structure
            cursor.execute("PRAGMA table_info(phases)")
            phase_cols = {row[1] for row in cursor.fetchall()}
            assert 'workflow_id' in phase_cols, "workflow_id missing from phases"
            assert 'status' in phase_cols, "status missing from phases"
            assert 'completed_at' in phase_cols, "completed_at missing from phases"
            print(f"✓ phases table columns: {phase_cols}")
            
            # Check tasks table structure
            cursor.execute("PRAGMA table_info(tasks)")
            task_cols = {row[1] for row in cursor.fetchall()}
            assert 'workflow_id' in task_cols, "workflow_id missing from tasks"
            assert 'task_id' in task_cols, "task_id missing from tasks"
            assert 'status' in task_cols, "status missing from tasks"
            print(f"✓ tasks table columns: {task_cols}")
        
        print("\n✅ Database schema test passed!\n")
        return True


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("RESUME CAPABILITY - IMPLEMENTATION VERIFICATION")
    print("=" * 70 + "\n")
    
    results = []
    
    # Run all tests
    results.append(("StateManager Methods", test_state_manager_resume_methods()))
    results.append(("WorkflowEngine Resume Parameter", test_workflow_engine_resume_flag()))
    results.append(("CLI Commands", test_cli_commands_exist()))
    results.append(("Database Schema", test_database_schema()))
    
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
        print("\n🎉 ALL TESTS PASSED - Resume capability is properly implemented!\n")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - Please review the implementation\n")
        sys.exit(1)
