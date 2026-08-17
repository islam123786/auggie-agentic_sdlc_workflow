"""
CLI interface for project automation
"""
import click
import sys
from pathlib import Path
from .workflow_engine import WorkflowEngine
from .config import Config


@click.group()
def cli():
    """Project Automation Orchestrator - AI-powered project development"""
    pass


@cli.command()
@click.option('--requirements', '-r', required=True, type=click.Path(exists=True),
              help='Path to project requirements markdown file')
@click.option('--workspace', '-w', default='./workspace',
              help='Workspace directory (default: ./workspace)')
@click.option('--config', '-c', default='config.yaml',
              help='Configuration file (default: config.yaml)')
@click.option('--github-repo', default=None,
              help='GitHub repository URL - automatically enables commit and push (e.g., https://github.com/user/repo.git)')
@click.option('--github-branch', default='main',
              help='Git branch to commit/push to (default: main)')
@click.option('--github-enable', is_flag=True,
              help='Enable git commits after each task (deprecated: use --github-repo instead)')
@click.option('--github-push', is_flag=True,
              help='Enable automatic push to GitHub (deprecated: use --github-repo instead)')
def run(requirements, workspace, config, github_enable, github_push, github_repo, github_branch):
    """Run complete project automation workflow

    Creates a complete, production-ready application using open-source technologies and Docker.

    The generated application:
      - Uses open-source stack (PostgreSQL, Redis, RabbitMQ, MinIO)
      - All services containerized with Docker
      - Works locally: `docker-compose up`
      - Cloud-ready: Deploy to any cloud (AWS, GCP, Azure, DigitalOcean)
      - No vendor lock-in
      - Easy to test and deploy

    Example:
      python3 -m orchestrator.cli run -r requirements.md -w ./workspace
    """

    click.echo("╔" + "═"*68 + "╗")
    click.echo("║" + " "*20 + "🤖 Project Automation Orchestrator" + " "*14 + "║")
    click.echo("╚" + "═"*68 + "╝")
    click.echo()
    click.echo(f"📋 Requirements: {requirements}")
    click.echo(f"📂 Workspace: {workspace}")
    click.echo(f"🐳 Architecture: Docker + Open-Source Stack")
    click.echo(f"   → PostgreSQL, Redis, RabbitMQ, MinIO")
    click.echo(f"   → Local testing with Docker Compose")
    click.echo()

    try:
        # Load config
        cfg = Config.from_file(config)
        cfg.workspace_root = workspace
        cfg.state_db_path = f"{workspace}/.state.db"  # Sync state_db_path with workspace

        # Override GitHub settings if provided via CLI
        # Auto-enable GitHub if repository URL is provided
        if github_repo:
            cfg.github_enabled = True
            cfg.github_auto_commit = True
            cfg.github_repository_url = github_repo
            cfg.github_branch = github_branch
            click.echo(f"📦 GitHub: Auto-commit and push enabled → {github_repo}")
        elif github_enable:
            cfg.github_enabled = True
            if github_push:
                cfg.github_auto_commit = True
                if cfg.github_repository_url:
                    click.echo(f"📦 GitHub: Auto-commit and push enabled → {cfg.github_repository_url}")
                else:
                    click.secho("⚠️  Warning: --github-push requires --github-repo", fg='yellow')
                    cfg.github_auto_commit = False
            else:
                click.echo("📦 GitHub: Local commits enabled (no push)")
        elif cfg.github_enabled:
            if cfg.github_auto_commit and cfg.github_repository_url:
                click.echo(f"📦 GitHub: Auto-commit and push enabled → {cfg.github_repository_url}")
            else:
                click.echo("📦 GitHub: Local commits enabled (no push)")

        # Run workflow
        engine = WorkflowEngine(cfg)
        result = engine.run_workflow(requirements)

        click.echo()
        click.echo("╔" + "═"*68 + "╗")
        click.echo("║" + " "*25 + "✅ SUCCESS!" + " "*32 + "║")
        click.echo("╚" + "═"*68 + "╝")
        click.echo()
        click.secho(f"Workflow ID: {result['workflow_id']}", fg='green')
        click.secho(f"Tasks: {result['tasks_completed']}", fg='green')
        click.secho(f"Project: {result['project_path']}", fg='cyan')
        click.secho(f"Artifacts: {result['artifacts_path']}", fg='cyan')

        # Show helpful next steps
        click.echo()
        click.secho("📌 Next Steps:", fg='yellow')
        click.echo("  • Review output: workspace/project-code/ and workspace/artifacts/")
        
    except Exception as e:
        click.echo()
        click.secho(f"❌ Error: {e}", fg='red', err=True)
        sys.exit(1)


@cli.command()
@click.argument('workflow_id', required=False)
@click.option('--workspace', '-w', required=True, help='Workspace directory path')
def status(workflow_id, workspace):
    """Check workflow status with detailed progress information

    If workflow_id is not provided, it will be loaded from workspace/.workflow_id file.
    """
    from .state_manager import StateManager
    from pathlib import Path

    # Auto-load workflow ID from file if not provided
    if not workflow_id:
        workflow_id_file = Path(workspace) / '.workflow_id'
        if workflow_id_file.exists():
            try:
                workflow_id = workflow_id_file.read_text().strip()
                click.echo(f"📂 Auto-loaded workflow ID from: {workflow_id_file}")
                click.echo()
            except Exception as e:
                click.secho(f"❌ Could not read workflow ID from {workflow_id_file}: {e}", fg='red', err=True)
                sys.exit(1)
        else:
            click.secho(f"❌ No workflow_id provided and {workflow_id_file} not found", fg='red', err=True)
            click.echo(f"   Either provide workflow_id as argument or ensure .workflow_id file exists")
            sys.exit(1)

    state = StateManager(f"{workspace}/.state.db")
    workflow = state.get_workflow(workflow_id)

    if not workflow:
        click.secho(f"Workflow {workflow_id} not found", fg='red', err=True)
        sys.exit(1)

    click.echo("╔" + "═"*68 + "╗")
    click.echo("║" + " "*22 + "📊 Workflow Status" + " "*27 + "║")
    click.echo("╚" + "═"*68 + "╝")
    click.echo()

    click.echo(f"🆔 Workflow ID: {workflow_id}")

    # Status with color
    status = workflow['status']
    status_color = 'green' if status == 'completed' else 'yellow' if status == 'running' else 'red' if status == 'failed' else 'cyan'
    click.echo("📊 Status: ", nl=False)
    click.secho(status.upper(), fg=status_color)

    click.echo(f"📌 Current Phase: {workflow['current_phase']}")
    click.echo(f"📋 Requirements: {workflow['requirements_path']}")
    click.echo(f"🕐 Created: {workflow['created_at']}")
    click.echo(f"🕐 Updated: {workflow['updated_at']}")

    if workflow['completed_at']:
        click.echo(f"✅ Completed: {workflow['completed_at']}")

    # Get completed tasks
    completed_tasks = state.get_completed_tasks(workflow_id)
    if completed_tasks:
        click.echo()
        click.secho(f"✓ Completed Tasks: {len(completed_tasks)}", fg='green')
        for task_id in completed_tasks[:5]:  # Show first 5
            click.echo(f"  • {task_id}")
        if len(completed_tasks) > 5:
            click.echo(f"  ... and {len(completed_tasks) - 5} more")

    # Show resume command if failed or paused
    if status in ['failed', 'paused']:
        click.echo()
        click.secho("💡 To resume this workflow:", fg='yellow')
        click.echo(f"   python3 -m orchestrator.cli resume {workflow_id} --workspace {workspace}")


@cli.command()
@click.option('--workspace', '-w', required=True, help='Workspace directory path')
@click.option('--limit', '-n', default=10, help='Number of workflows to show')
def list(workspace, limit):
    """List recent workflows with their status"""
    from .state_manager import StateManager

    state = StateManager(f"{workspace}/.state.db")
    workflows = state.list_workflows(limit)

    if not workflows:
        click.echo("No workflows found")
        click.echo()
        click.echo("💡 To start a new workflow:")
        click.echo(f"   python3 -m orchestrator.cli run --requirements <file> --workspace {workspace}")
        return

    click.echo("╔" + "═"*68 + "╗")
    click.echo("║" + " "*24 + "📋 Workflows" + " "*32 + "║")
    click.echo("╚" + "═"*68 + "╝")
    click.echo()

    click.echo(f"{'ID':<38} {'Status':<12} {'Phase':<15} {'Created'}")
    click.echo("─" * 100)

    for wf in workflows:
        wf_id = wf['id'][:36]
        status = wf['status']
        status_color = 'green' if status == 'completed' else 'yellow' if status == 'running' else 'red' if status == 'failed' else 'cyan'
        phase = (wf['current_phase'] or 'N/A')[:14]

        click.echo(f"{wf_id:<38} ", nl=False)
        click.secho(f"{status:<12}", fg=status_color, nl=False)
        click.echo(f" {phase:<15} {wf['created_at']}")

    click.echo()
    click.echo("💡 Commands:")
    click.echo(f"   • View status: python3 -m orchestrator.cli status <workflow-id> --workspace {workspace}")
    click.echo(f"   • Resume failed: python3 -m orchestrator.cli resume <workflow-id> --workspace {workspace}")


@cli.command()
@click.argument('workflow_id', required=False)
@click.option('--workspace', '-w', required=True,
              help='Workspace directory path (must match the path used in run command)')
@click.option('--config', '-c', default='config.yaml', help='Configuration file path')
@click.option('--github-repo', default=None,
              help='GitHub repository URL (auto-enables GitHub integration)')
@click.option('--github-branch', default='main',
              help='Git branch to commit/push to (default: main)')
def approve(workflow_id, workspace, config, github_repo, github_branch):
    """Approve architecture design and continue workflow"""
    from .state_manager import StateManager
    from .config import Config
    from pathlib import Path

    click.echo("╔" + "═"*68 + "╗")
    click.echo("║" + " "*18 + "✅ Architecture Approval" + " "*24 + "║")
    click.echo("╚" + "═"*68 + "╝")
    click.echo()

    # Auto-load workflow ID from file if not provided
    if not workflow_id:
        workflow_id_file = Path(workspace) / '.workflow_id'
        if workflow_id_file.exists():
            try:
                workflow_id = workflow_id_file.read_text().strip()
                click.echo(f"📂 Auto-loaded workflow ID from: {workflow_id_file}")
                click.echo(f"   Workflow ID: {workflow_id}")
                click.echo()
            except Exception as e:
                click.secho(f"❌ Could not read workflow ID from {workflow_id_file}: {e}", fg='red', err=True)
                sys.exit(1)
        else:
            click.secho(f"❌ No workflow_id provided and {workflow_id_file} not found", fg='red', err=True)
            click.echo(f"   Either provide workflow_id as argument or ensure .workflow_id file exists")
            sys.exit(1)

    state = StateManager(f"{workspace}/.state.db")
    workflow = state.get_workflow(workflow_id)

    if not workflow:
        click.secho(f"❌ Workflow {workflow_id} not found", fg='red', err=True)
        sys.exit(1)

    # Check current status
    if workflow['status'] not in ['running', 'paused']:
        click.secho(f"❌ Workflow is {workflow['status']}, cannot approve", fg='red', err=True)
        sys.exit(1)

    # Approve architecture
    state.approve_architecture(workflow_id)
    click.secho("✅ Architecture approved!", fg='green')
    click.echo()
    click.echo("Continuing workflow...")
    click.echo()

    # Load config and continue workflow with correct workspace
    cfg = Config.from_file(config)
    cfg.workspace_root = workspace
    cfg.state_db_path = f"{workspace}/.state.db"  # Update state_db_path to match workspace

    # Override GitHub settings if provided via CLI, otherwise restore from workflow state
    if github_repo:
        # CLI parameter overrides workflow state
        cfg.github_enabled = True
        cfg.github_auto_commit = True
        cfg.github_repository_url = github_repo
        cfg.github_branch = github_branch
        click.echo(f"📦 GitHub: Auto-commit and push enabled → {github_repo}")
        click.echo()
    else:
        # Restore GitHub config from workflow state
        if workflow.get('github_enabled'):
            cfg.github_enabled = bool(workflow['github_enabled'])
            cfg.github_auto_commit = bool(workflow.get('github_auto_commit', 0))
            cfg.github_repository_url = workflow.get('github_repository_url')
            cfg.github_branch = workflow.get('github_branch', 'main')
            if cfg.github_repository_url:
                click.echo(f"📦 GitHub: Restored from workflow state → {cfg.github_repository_url}")
                click.echo()

    engine = WorkflowEngine(cfg)

    # Get requirements path from workflow
    requirements_path = workflow['requirements_path']

    # Continue from where it left off (resume with existing workflow_id)
    try:
        result = engine.run_workflow(requirements_path, workflow_id=workflow_id)
        click.echo()
        click.secho("✅ Workflow completed successfully!", fg='green')
        # Safely access result keys with defaults
        if 'project_path' in result:
            click.echo(f"📦 Project: {result['project_path']}")
        if 'artifacts_path' in result:
            click.echo(f"📄 Artifacts: {result['artifacts_path']}")
    except Exception as e:
        click.secho(f"❌ Workflow failed: {e}", fg='red', err=True)
        sys.exit(1)


@cli.command()
@click.argument('workflow_id', required=False)
@click.option('--feedback', '-f', required=True, help='Feedback on why architecture was rejected')
@click.option('--workspace', '-w', required=True, help='Workspace directory path (must match the path used in run command)')
@click.option('--config', '-c', default='config.yaml', help='Configuration file path')
def reject(workflow_id, feedback, workspace, config):
    """Reject architecture design with feedback and regenerate

    If workflow_id is not provided, it will be loaded from workspace/.workflow_id file.
    """
    from .state_manager import StateManager
    from .config import Config
    from pathlib import Path
    import os

    click.echo("╔" + "═"*68 + "╗")
    click.echo("║" + " "*18 + "❌ Architecture Rejection" + " "*23 + "║")
    click.echo("╚" + "═"*68 + "╝")
    click.echo()

    # Auto-load workflow ID from file if not provided
    if not workflow_id:
        workflow_id_file = Path(workspace) / '.workflow_id'
        if workflow_id_file.exists():
            try:
                workflow_id = workflow_id_file.read_text().strip()
                click.echo(f"📂 Auto-loaded workflow ID from: {workflow_id_file}")
                click.echo(f"   Workflow ID: {workflow_id}")
                click.echo()
            except Exception as e:
                click.secho(f"❌ Could not read workflow ID from {workflow_id_file}: {e}", fg='red', err=True)
                sys.exit(1)
        else:
            click.secho(f"❌ No workflow_id provided and {workflow_id_file} not found", fg='red', err=True)
            click.echo(f"   Either provide workflow_id as argument or ensure .workflow_id file exists")
            sys.exit(1)

    state = StateManager(f"{workspace}/.state.db")
    workflow = state.get_workflow(workflow_id)

    if not workflow:
        click.secho(f"❌ Workflow {workflow_id} not found", fg='red', err=True)
        sys.exit(1)

    # Reject architecture in database
    state.reject_architecture(workflow_id, feedback)
    click.secho("❌ Architecture rejected", fg='yellow')
    click.echo()
    click.echo(f"📝 Feedback: {feedback}")
    click.echo()

    # Delete existing architecture.md file
    architecture_file = Path(workspace) / 'artifacts' / 'architecture.md'
    if architecture_file.exists():
        click.echo(f"🗑️  Deleting existing architecture file...")
        os.remove(architecture_file)
        click.secho("   ✓ architecture.md deleted", fg='green')
        click.echo()

    # Load config and regenerate architecture
    click.echo("🔄 Regenerating architecture with your feedback...")
    click.echo()

    cfg = Config.from_file(config)
    cfg.workspace_root = workspace
    cfg.state_db_path = f"{workspace}/.state.db"

    engine = WorkflowEngine(cfg)

    # Get requirements path from workflow
    requirements_path = workflow['requirements_path']

    try:
        # Re-run architecture design with feedback
        engine._run_agent1_architecture_with_feedback(workflow_id, requirements_path, feedback)

        # Mark as awaiting approval again
        state.update_phase(workflow_id, "architecture", {
            "status": "awaiting_approval",
            "regeneration_count": state.get_architecture_regeneration_count(workflow_id) + 1
        })

        click.echo()
        click.secho("✅ New architecture design generated!", fg='green')
        click.echo()
        click.echo(f"📄 New architecture: {architecture_file}")
        click.echo()
        click.echo("Please review and then:")
        click.echo(f"  ✅ Approve: python3 -m orchestrator.cli approve {workflow_id} --workspace {workspace}")
        click.echo(f"  ❌ Reject:  python3 -m orchestrator.cli reject {workflow_id} --workspace {workspace} --feedback \"your feedback\"")

    except Exception as e:
        click.secho(f"❌ Failed to regenerate architecture: {e}", fg='red', err=True)
        sys.exit(1)


@cli.command()
@click.argument('workflow_id', required=False)
@click.option('--workspace', '-w', required=True, help='Workspace directory path (must match the path used in run command)')
@click.option('--config', '-c', default='config.yaml', help='Configuration file path')
@click.option('--github-repo', default=None,
              help='GitHub repository URL - automatically enables commit and push')
@click.option('--github-branch', default='main',
              help='Git branch to commit/push to (default: main)')
@click.option('--github-enable', is_flag=True,
              help='Enable git commits after each task (deprecated: use --github-repo instead)')
@click.option('--github-push', is_flag=True,
              help='Enable automatic push to GitHub (deprecated: use --github-repo instead)')
def resume(workflow_id, workspace, config, github_enable, github_push, github_repo, github_branch):
    """Resume a failed or paused workflow from where it stopped

    If workflow_id is not provided, it will be loaded from workspace/.workflow_id file.
    """
    from .state_manager import StateManager
    from .config import Config
    from pathlib import Path

    click.echo("╔" + "═"*68 + "╗")
    click.echo("║" + " "*20 + "🔄 Resume Workflow" + " "*28 + "║")
    click.echo("╚" + "═"*68 + "╝")
    click.echo()

    # Auto-load workflow ID from file if not provided
    if not workflow_id:
        workflow_id_file = Path(workspace) / '.workflow_id'
        if workflow_id_file.exists():
            try:
                workflow_id = workflow_id_file.read_text().strip()
                click.echo(f"📂 Auto-loaded workflow ID from: {workflow_id_file}")
                click.echo(f"   Workflow ID: {workflow_id}")
                click.echo()
            except Exception as e:
                click.secho(f"❌ Could not read workflow ID from {workflow_id_file}: {e}", fg='red', err=True)
                sys.exit(1)
        else:
            click.secho(f"❌ No workflow_id provided and {workflow_id_file} not found", fg='red', err=True)
            click.echo(f"   Either provide workflow_id as argument or ensure .workflow_id file exists")
            sys.exit(1)

    state = StateManager(f"{workspace}/.state.db")
    workflow = state.get_workflow(workflow_id)

    if not workflow:
        click.secho(f"❌ Workflow {workflow_id} not found", fg='red', err=True)
        sys.exit(1)

    # Check if workflow can be resumed
    if workflow['status'] not in ['failed', 'paused', 'running']:
        click.secho(f"❌ Cannot resume workflow with status '{workflow['status']}'", fg='red', err=True)
        click.echo(f"   Only failed, paused, or running workflows can be resumed")
        sys.exit(1)

    click.echo(f"📋 Workflow ID: {workflow_id}")
    click.echo(f"📂 Workspace: {workspace}")
    click.echo(f"📊 Current Status: {workflow['status']}")
    click.echo(f"📌 Current Phase: {workflow['current_phase']}")
    click.echo()

    # Get completed tasks
    completed_tasks = state.get_completed_tasks(workflow_id)
    if completed_tasks:
        click.secho(f"✓ {len(completed_tasks)} tasks already completed", fg='green')
        click.echo()

    click.echo("Resuming workflow from where it stopped...")
    click.echo("(Completed steps will be skipped)")
    click.echo()

    # Load config and resume workflow
    cfg = Config.from_file(config)
    cfg.workspace_root = workspace
    cfg.state_db_path = f"{workspace}/.state.db"  # Sync state_db_path with workspace

    # Override GitHub settings if provided via CLI, otherwise restore from workflow state
    if github_repo:
        # CLI parameter overrides workflow state
        cfg.github_enabled = True
        cfg.github_auto_commit = True
        cfg.github_repository_url = github_repo
        cfg.github_branch = github_branch
        click.echo(f"📦 GitHub: Auto-commit and push enabled → {github_repo}")
    elif github_enable:
        cfg.github_enabled = True
        if github_push:
            cfg.github_auto_commit = True
            if cfg.github_repository_url:
                click.echo(f"📦 GitHub: Auto-commit and push enabled → {cfg.github_repository_url}")
            else:
                click.secho("⚠️  Warning: --github-push requires --github-repo", fg='yellow')
                cfg.github_auto_commit = False
        else:
            click.echo("📦 GitHub: Local commits enabled (no push)")
    else:
        # Restore GitHub config from workflow state
        if workflow.get('github_enabled'):
            cfg.github_enabled = bool(workflow['github_enabled'])
            cfg.github_auto_commit = bool(workflow.get('github_auto_commit', 0))
            cfg.github_repository_url = workflow.get('github_repository_url')
            cfg.github_branch = workflow.get('github_branch', 'main')
            if cfg.github_repository_url:
                click.echo(f"📦 GitHub: Restored from workflow state → {cfg.github_repository_url}")

    engine = WorkflowEngine(cfg)

    # Get requirements path from workflow
    requirements_path = workflow['requirements_path']

    # Resume workflow with resume=True flag
    try:
        result = engine.run_workflow(requirements_path, workflow_id=workflow_id, resume=True)
        click.echo()
        click.secho("✅ Workflow completed successfully!", fg='green')
        if 'project_path' in result:
            click.echo(f"📦 Project: {result['project_path']}")
        if 'artifacts_path' in result:
            click.echo(f"📄 Artifacts: {result['artifacts_path']}")
    except Exception as e:
        click.secho(f"❌ Workflow failed: {e}", fg='red', err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
def version():
    """Show version information"""
    from . import __version__
    click.echo(f"Project Automation Orchestrator v{__version__}")


@cli.command()
@click.argument('workflow_id', required=False)
@click.option('--workspace', '-w', default='./workspace',
              help='Workspace directory (default: ./workspace)')
def status(workflow_id, workspace):
    """Show detailed status of workflow and all tasks

    Displays current status, phase, and progress of all tasks in the workflow.
    Useful for tracking progress and identifying which task failed.

    If workflow_id is not provided, it will be loaded from workspace/.workflow_id file.
    """
    from .state_manager import StateManager
    from pathlib import Path

    click.echo("╔" + "═"*68 + "╗")
    click.echo("║" + " "*22 + "📊 Workflow Status" + " "*27 + "║")
    click.echo("╚" + "═"*68 + "╝")
    click.echo()

    # Auto-load workflow ID from file if not provided
    if not workflow_id:
        workflow_id_file = Path(workspace) / '.workflow_id'
        if workflow_id_file.exists():
            try:
                workflow_id = workflow_id_file.read_text().strip()
                click.echo(f"📂 Auto-loaded workflow ID from: {workflow_id_file}")
                click.echo(f"   Workflow ID: {workflow_id}")
                click.echo()
            except Exception as e:
                click.secho(f"❌ Could not read workflow ID from {workflow_id_file}: {e}", fg='red', err=True)
                sys.exit(1)
        else:
            click.secho(f"❌ No workflow_id provided and {workflow_id_file} not found", fg='red', err=True)
            click.echo(f"   Either provide workflow_id as argument or ensure .workflow_id file exists")
            sys.exit(1)

    state = StateManager(f"{workspace}/.state.db")
    workflow = state.get_workflow(workflow_id)

    if not workflow:
        click.secho(f"❌ Workflow {workflow_id} not found", fg='red', err=True)
        sys.exit(1)

    # Display workflow info
    click.echo("═" * 70)
    click.echo("WORKFLOW INFORMATION")
    click.echo("═" * 70)
    click.echo(f"  ID: {workflow['id']}")
    click.echo(f"  Status: {workflow['status'].upper()}")
    click.echo(f"  Current Phase: {workflow['current_phase']}")
    click.echo(f"  Created: {workflow['created_at']}")
    click.echo(f"  Updated: {workflow['updated_at']}")
    if workflow['completed_at']:
        click.echo(f"  Completed: {workflow['completed_at']}")
    click.echo(f"  GitHub Enabled: {'Yes' if workflow['github_enabled'] else 'No'}")
    if workflow['github_repository_url']:
        click.echo(f"  GitHub Repo: {workflow['github_repository_url']}")
        click.echo(f"  GitHub Branch: {workflow['github_branch']}")
    click.echo()

    # Get all tasks
    all_tasks = state.get_all_tasks_status(workflow_id)

    if not all_tasks:
        click.echo("ℹ️  No tasks found for this workflow yet")
        return

    # Display tasks status
    click.echo("═" * 70)
    click.echo("TASKS STATUS")
    click.echo("═" * 70)
    click.echo()

    completed_count = sum(1 for t in all_tasks if t['status'] == 'completed')
    running_count = sum(1 for t in all_tasks if t['status'] == 'running')
    failed_count = sum(1 for t in all_tasks if t['status'] == 'failed')
    total_count = len(all_tasks)

    click.echo(f"  Total: {total_count} tasks")
    click.echo(f"  ✅ Completed: {completed_count}")
    click.echo(f"  ⚙️  Running: {running_count}")
    click.echo(f"  ❌ Failed: {failed_count}")
    click.echo()

    # Display each task
    for i, task in enumerate(all_tasks, 1):
        status_emoji = {
            'completed': '✅',
            'running': '⚙️ ',
            'failed': '❌'
        }.get(task['status'], '❓')

        phase_emoji = {
            'implementation': '🔨',
            'testing': '🧪',
            'documentation': '📝',
            'completed': '✅'
        }.get(task['current_phase'], '📌')

        click.echo(f"{status_emoji} Task {i}: {task['task_id']}")
        if task['task_title']:
            click.echo(f"     Title: {task['task_title']}")
        click.echo(f"     Status: {task['status'].upper()}")
        click.echo(f"     Phase: {phase_emoji} {task['current_phase']}")
        if task['started_at']:
            click.echo(f"     Started: {task['started_at']}")
        if task['completed_at']:
            click.echo(f"     Completed: {task['completed_at']}")
        if task['failed_at']:
            click.echo(f"     Failed: {task['failed_at']}")
        if task['error_message']:
            error_preview = task['error_message'][:150] + "..." if len(task['error_message']) > 150 else task['error_message']
            click.echo(f"     Error: {error_preview}")
        click.echo()

    # Show resume hint if there's a failed task
    if failed_count > 0:
        last_failed = state.get_last_failed_task(workflow_id)
        click.echo("═" * 70)
        click.echo("💡 RESUME HINT")
        click.echo("═" * 70)
        click.echo(f"  Last failed task: {last_failed['task_id']}")
        click.echo(f"  Failed in: {last_failed['current_phase']} phase")
        click.echo()
        click.echo("  To resume this workflow, run:")
        click.echo(f"    python3 -m orchestrator.cli resume {workflow_id} --workspace {workspace}")
        click.echo()


if __name__ == '__main__':
    cli()
