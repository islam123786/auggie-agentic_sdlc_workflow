"""
Main workflow engine for project automation
"""
import json
import subprocess
import sys
import platform
import shutil
from pathlib import Path
from typing import Dict, List, Any
from .state_manager import StateManager
from .config import Config


class WorkflowEngine:
    """Orchestrates the complete workflow"""

    def __init__(self, config: Config):
        self.config = config
        self.state = StateManager(config.state_db_path)
        self.workspace = Path(config.workspace_root)
        self.agents_dir = Path(config.agents_dir)
        self.is_wsl = False  # Will be set by _find_bash_executable
        self.bash_executable = self._find_bash_executable()
        self.project_code_dir = self.workspace / 'project-code'

    @staticmethod
    def _validate_tasks_json(tasks_data: Dict[str, Any]) -> List[str]:
        """Validate tasks.json structure and return list of errors"""
        errors = []

        # Check required top-level fields
        required_fields = ['project_name', 'tasks']
        for field in required_fields:
            if field not in tasks_data:
                errors.append(f"Missing required field: {field}")

        # Validate tasks array
        if 'tasks' not in tasks_data:
            return errors  # Can't continue without tasks

        tasks = tasks_data.get('tasks')
        if not isinstance(tasks, list):
            errors.append(f"'tasks' must be an array, got {type(tasks).__name__}")
            return errors

        # Validate each task
        required_task_fields = ['id', 'title', 'description', 'sequence', 'category']
        valid_categories = ['setup', 'infrastructure', 'implementation', 'integration', 'testing', 'documentation']

        for idx, task in enumerate(tasks):
            if not isinstance(task, dict):
                errors.append(f"Task {idx} must be an object, got {type(task).__name__}")
                continue

            # Check required fields
            for field in required_task_fields:
                if field not in task:
                    errors.append(f"Task {idx} ({task.get('id', 'unknown')}): missing field '{field}'")

            # Validate category
            if 'category' in task and task['category'] not in valid_categories:
                errors.append(f"Task {idx} ({task.get('id', 'unknown')}): invalid category '{task['category']}', must be one of {valid_categories}")

            # Validate sequence is a number
            if 'sequence' in task and not isinstance(task['sequence'], (int, float)):
                errors.append(f"Task {idx} ({task.get('id', 'unknown')}): sequence must be a number, got {type(task['sequence']).__name__}")

        return errors

    def _find_bash_executable(self) -> str:
        """Find bash executable, prioritizing Git Bash on Windows"""
        if platform.system() == "Windows":
            # Try Git Bash first (common location)
            git_bash_paths = [
                r"C:\Program Files\Git\bin\bash.exe",
                r"C:\Program Files (x86)\Git\bin\bash.exe",
            ]
            for path in git_bash_paths:
                if Path(path).exists():
                    self.is_wsl = False
                    return path

            # Try to find bash in PATH
            bash_path = shutil.which("bash")
            if bash_path:
                # Check if it's WSL bash (usually in WindowsApps)
                self.is_wsl = "WindowsApps" in bash_path or "wsl" in bash_path.lower()
                return bash_path

            # Last resort: check for WSL
            wsl_path = shutil.which("wsl")
            if wsl_path:
                self.is_wsl = True
                return "wsl"

            raise RuntimeError(
                "Bash not found on Windows. Please install Git for Windows "
                "(https://git-scm.com/download/win) or WSL to run this tool."
            )
        else:
            # On Unix-like systems, bash should be available
            self.is_wsl = False
            bash_path = shutil.which("bash")
            if bash_path:
                return bash_path
            raise RuntimeError("Bash not found. Please install bash.")

    def _convert_path_for_bash(self, path: str) -> str:
        """Convert Windows path to format suitable for bash"""
        if platform.system() != "Windows":
            return path

        path_obj = Path(path).absolute()

        if self.is_wsl:
            # Convert Windows path to WSL path: C:\foo\bar -> /mnt/c/foo/bar
            path_str = str(path_obj)
            if len(path_str) > 1 and path_str[1] == ':':
                drive = path_str[0].lower()
                rest = path_str[2:].replace('\\', '/')
                return f"/mnt/{drive}{rest}"

        # For Git Bash, just use forward slashes
        return str(path_obj).replace('\\', '/')

    def _save_workflow_id(self, workflow_id: str):
        """Save workflow ID to a file in workspace for easy access"""
        workflow_id_file = self.workspace / '.workflow_id'
        try:
            with open(workflow_id_file, 'w') as f:
                f.write(workflow_id)
        except Exception as e:
            # Non-fatal, just log
            print(f"⚠️  Warning: Could not save workflow ID to file: {e}")

    def _load_workflow_id(self) -> str:
        """Load workflow ID from workspace file"""
        workflow_id_file = self.workspace / '.workflow_id'
        if workflow_id_file.exists():
            try:
                with open(workflow_id_file, 'r') as f:
                    return f.read().strip()
            except Exception:
                pass
        return None

    def run_workflow(self, requirements_path: str, workflow_id: str = None, resume: bool = False) -> Dict:
        """Execute project automation workflow

        Args:
            requirements_path: Path to requirements file
            workflow_id: Optional existing workflow ID to resume (for approval continuation)
            resume: If True, resume from where the workflow stopped (skip completed phases/tasks)
        """
        if workflow_id is None:
            # Create workflow with GitHub configuration
            workflow_id = self.state.create_workflow(
                requirements_path,
                github_enabled=self.config.github_enabled,
                github_auto_commit=self.config.github_auto_commit,
                github_repository_url=self.config.github_repository_url,
                github_branch=self.config.github_branch
            )
            print(f"🚀 Starting workflow: {workflow_id}")
            # Save workflow ID to file for easy access
            self._save_workflow_id(workflow_id)
            resume = False  # New workflow, nothing to resume
        else:
            if resume:
                # Try to resume the workflow
                try:
                    self.state.resume_workflow(workflow_id)
                    print(f"🔄 Resuming workflow: {workflow_id}")
                except ValueError as e:
                    print(f"⚠️  {e}")
                    print(f"🔄 Continuing workflow: {workflow_id}")
            else:
                print(f"🔄 Continuing workflow: {workflow_id}")
            # Update saved workflow ID
            self._save_workflow_id(workflow_id)

        print(f"📋 Requirements: {requirements_path}")
        print(f"📂 Workspace: {self.workspace}")
        print(f"💾 Workflow ID saved to: {self.workspace}/.workflow_id")

        # Get resume information if resuming
        last_completed_phase = None
        completed_tasks = []
        if resume:
            last_completed_phase = self.state.get_last_completed_phase(workflow_id)
            completed_tasks = self.state.get_completed_tasks(workflow_id)
            if last_completed_phase:
                print(f"📌 Last completed phase: {last_completed_phase}")
            if completed_tasks:
                print(f"✓ {len(completed_tasks)} tasks already completed")

                # Sync tasks.md and tasks.json with database state
                print(f"🔄 Syncing task files with database state...")
                for task_id in completed_tasks:
                    self._update_tasks_md(task_id)
                print(f"✓ Task files synchronized")

        try:
            # Step 1: Architecture Design
            architecture_approved = self.state.get_architecture_status(workflow_id)

            if not architecture_approved:
                print("\n" + "="*70)
                print("STEP 1: ARCHITECTURE DESIGN")
                print("="*70)

                self._run_agent1_architecture(workflow_id, requirements_path)
                self.state.update_phase(workflow_id, "architecture", {
                    "status": "awaiting_approval"
                })

                print("\n" + "="*70)
                print("⏸️  WORKFLOW PAUSED - ARCHITECTURE APPROVAL REQUIRED")
                print("="*70)
                print(f"\n📄 Architecture document: {self.workspace / 'artifacts' / 'architecture.md'}")
                print(f"\nPlease review and then:")
                print(f"  ✅ Approve: python3 -m orchestrator.cli approve {workflow_id} --workspace {self.workspace}")
                print(f"  ❌ Reject:  python3 -m orchestrator.cli reject {workflow_id} --workspace {self.workspace} --feedback \"your feedback\"")
                print("\n" + "="*70)

                return {
                    "workflow_id": workflow_id,
                    "status": "awaiting_architecture_approval",
                    "architecture_path": str(self.workspace / 'artifacts' / 'architecture.md'),
                    "tasks_completed": 0,
                    "project_path": str(self.workspace / 'project-code'),
                    "artifacts_path": str(self.workspace / 'artifacts')
                }
            else:
                print("\n✓ Architecture already approved, proceeding...")

            # Step 2: Task Planning
            print("\n" + "="*70)
            print("STEP 2: TASK PLANNING")
            print("="*70)

            # Check if task planning already completed when resuming
            if resume and last_completed_phase and last_completed_phase in ['task_planning', 'setup', 'implementation', 'testing', 'documentation', 'completed']:
                print("✓ Task planning already complete (skipping)")
                # Load existing tasks from tasks.json
                tasks_file = self.workspace / 'artifacts' / 'tasks.json'
                if tasks_file.exists():
                    import json
                    with open(tasks_file, 'r') as f:
                        tasks_data = json.load(f)
                        all_tasks = tasks_data.get('tasks', [])
                    print(f"✓ Loaded {len(all_tasks)} existing tasks from tasks.json")
                else:
                    print("⚠️  Warning: tasks.json not found, regenerating tasks...")
                    all_tasks = self._run_agent2_task_planning(workflow_id, requirements_path)
                    self.state.update_phase(workflow_id, "task_planning", {
                        "tasks_count": len(all_tasks),
                        "status": "completed"
                    })
                    print(f"✓ Generated {len(all_tasks)} tasks")
            else:
                # Generate tasks from requirements
                all_tasks = self._run_agent2_task_planning(workflow_id, requirements_path)
                self.state.update_phase(workflow_id, "task_planning", {
                    "tasks_count": len(all_tasks),
                    "status": "completed"
                })
                print(f"✓ Generated {len(all_tasks)} tasks")

            # Step 3: Use tasks
            tasks = all_tasks

            if not tasks:
                print(f"⚠️  Warning: No tasks generated")
                return {
                    "workflow_id": workflow_id,
                    "status": "completed",
                    "tasks_completed": 0,
                    "project_path": str(self.workspace / 'project-code'),
                    "artifacts_path": str(self.workspace / 'artifacts')
                }

            # Step 4: Environment Setup
            if resume and last_completed_phase and last_completed_phase in ['setup', 'implementation', 'completed']:
                print("\n" + "="*70)
                print(f"STEP 3: ENVIRONMENT SETUP")
                print("="*70)
                print("✓ Environment setup already complete (skipping)")
            else:
                print("\n" + "="*70)
                print(f"STEP 3: ENVIRONMENT SETUP")
                print("="*70)
                self._run_agent3_setup(workflow_id, requirements_path)
                self.state.update_phase(workflow_id, "setup", {"status": "completed"})
                print("✓ Environment setup complete")

            # Step 5: Implementation Loop
            print("\n" + "="*70)
            print(f"STEP 4: TASK IMPLEMENTATION")
            print("="*70)
            for idx, task in enumerate(tasks, 1):
                task_id = task['id']
                task_title = task['title']

                # Skip already completed tasks when resuming
                if resume and task_id in completed_tasks:
                    print(f"\n{'─'*70}")
                    print(f"⏭️  Task {idx}/{len(tasks)}: {task_title} (already completed)")
                    print(f"   ID: {task_id}")
                    print(f"{'─'*70}")
                    continue

                print(f"\n{'─'*70}")
                print(f"📌 Task {idx}/{len(tasks)}: {task_title}")
                print(f"   ID: {task_id}")
                print(f"{'─'*70}")

                # Check if task was previously started and determine resume point
                resume_from_phase = None
                if resume:
                    task_status = self.state.get_task_status(workflow_id, task_id)
                    if task_status and task_status['status'] in ['running', 'failed']:
                        resume_from_phase = task_status['current_phase']
                        print(f"  🔄 Resuming from phase: {resume_from_phase}")
                        print(f"  💾 Previous status: {task_status['status']}")
                        if task_status.get('error_message'):
                            print(f"  📋 Previous error: {task_status['error_message'][:100]}...")

                try:
                    # Start task in database (or update if resuming)
                    if not resume_from_phase:
                        # Fresh start - begin from implementation
                        self.state.start_task(workflow_id, task_id, task_title, preserve_phase=False)
                        print(f"  💾 Task started and tracked in database")
                        print(f"  💾 Status: running, Phase: implementation")
                    else:
                        # Resuming - keep the current phase, just reset status to running
                        self.state.start_task(workflow_id, task_id, task_title, preserve_phase=True)
                        print(f"  💾 Task status reset to running (phase preserved: {resume_from_phase})")

                    # Agent 3: Implement task
                    if not resume_from_phase or resume_from_phase == 'implementation':
                        print("  ⚙️  Implementing...")
                        self._run_agent3_implement(workflow_id, task_id, requirements_path)
                        print("  ✓ Implementation complete")

                        # Update phase to testing
                        self.state.update_task_phase(workflow_id, task_id, "testing")
                        print(f"  💾 Phase: implementation → testing")
                    else:
                        print(f"  ⏭️  Skipping implementation (already completed)")
                        print(f"  💾 Current phase in DB: {resume_from_phase}")

                    # Agent 4: Test task
                    if not resume_from_phase or resume_from_phase in ['implementation', 'testing']:
                        if resume_from_phase == 'testing':
                            print("  🧪 Testing (resuming from here)...")
                            print(f"  💾 Current phase in DB: testing")
                        else:
                            print("  🧪 Testing...")
                        self._run_agent4_testing(workflow_id, task_id)
                        print("  ✓ Tests complete")

                        # Update phase to documentation
                        self.state.update_task_phase(workflow_id, task_id, "documentation")
                        print(f"  💾 Phase: testing → documentation")
                    else:
                        print(f"  ⏭️  Skipping testing (already completed)")
                        print(f"  💾 Current phase in DB: {resume_from_phase}")

                    # Agent 5: Document task
                    if not resume_from_phase or resume_from_phase in ['implementation', 'testing', 'documentation']:
                        if resume_from_phase == 'documentation':
                            print("  📝 Documenting (resuming from here)...")
                            print(f"  💾 Current phase in DB: documentation")
                        else:
                            print("  📝 Documenting...")
                        self._run_agent5_documentation(workflow_id, task_id)
                        print("  ✓ Documentation complete")
                    else:
                        print(f"  ⏭️  Skipping documentation (already completed)")

                    # Git: Commit task if enabled
                    print(f"  🔍 DEBUG: github_enabled={self.config.github_enabled}, github_repo='{self.config.github_repository_url}'")
                    if self.config.github_enabled:
                        self._git_commit_task(task_id, task_title)
                    else:
                        print(f"  ⚠️  GitHub commit SKIPPED - github_enabled is False")
                        print(f"     To enable: use --github-repo parameter when running workflow")

                    # Mark task as completed in database
                    self.state.complete_task(workflow_id, task_id)
                    print(f"  💾 Status: running → completed")

                    # Update tasks.md to mark task as complete
                    self._update_tasks_md(task_id)

                    print(f"  ✅ Task {task_id} fully completed")

                except Exception as e:
                    # Determine which phase failed based on the error
                    task_status = self.state.get_task_status(workflow_id, task_id)
                    failed_phase = task_status['current_phase'] if task_status else 'implementation'

                    # Mark task as failed in database
                    error_msg = str(e)
                    self.state.fail_task(workflow_id, task_id, failed_phase, error_msg)
                    print(f"  ❌ Task {task_id} FAILED in {failed_phase} phase")
                    print(f"  💾 Status: running → failed")
                    print(f"  💾 Error: {error_msg[:100]}...")

                    # Re-raise to fail the workflow
                    raise
            
            # Mark as completed
            self.state.mark_completed(workflow_id)

            print("\n" + "="*70)
            print(f"✅ WORKFLOW COMPLETED SUCCESSFULLY")
            print("="*70)
            print(f"Workflow ID: {workflow_id}")
            print(f"Tasks: {len(tasks)}")
            print(f"Project location: {self.workspace / 'project-code'}")
            print(f"Artifacts location: {self.workspace / 'artifacts'}")

            print("\n💡 Next Steps:")
            print("   1. Review output in workspace/project-code/ and workspace/artifacts/")
            print("   2. Test locally: cd workspace/project-code/ && docker-compose up")

            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "tasks_completed": len(tasks),
                "project_path": str(self.workspace / 'project-code'),
                "artifacts_path": str(self.workspace / 'artifacts')
            }

        except Exception as e:
            self.state.mark_failed(workflow_id, str(e))
            print(f"\n❌ Workflow failed")
            print(f"   Workflow ID: {workflow_id}")
            print(f"   Error: {e}")
            print(f"\n💡 Tip: Check logs above for details on which agent failed")
            raise RuntimeError(f"Workflow {workflow_id} failed: {e}") from e

    def run_complete_workflow(self, requirements_path: str) -> Dict:
        """Execute complete project automation workflow

        Backwards-compatible method.
        """
        return self.run_workflow(requirements_path)
    
    def _run_agent1_architecture(self, workflow_id: str, requirements: str):
        """Run Agent 1: Architecture Design"""
        artifacts_dir = self.workspace / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        print("")
        print("🏗️  Designing system architecture...")
        print("🤖 Agent 1 (Architecture) is analyzing requirements and selecting tech stack...")
        print("🐳 Target: Docker + Open-Source Stack (PostgreSQL, Redis, RabbitMQ, MinIO)")
        print("")
        sys.stdout.flush()

        try:
            cmd = [
                self.bash_executable,
                self._convert_path_for_bash(str(self.agents_dir / "agent1_architecture.sh")),
                "--requirements-path", self._convert_path_for_bash(requirements),
                "--workspace-root", self._convert_path_for_bash(str(self.workspace)),
                "--output-dir", self._convert_path_for_bash(str(artifacts_dir))
            ]

            subprocess.run(cmd, check=True, timeout=self.config.timeout_seconds)
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Agent 1 (Architecture) timed out after {self.config.timeout_seconds}s for workflow {workflow_id}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Agent 1 (Architecture) failed with exit code {e.returncode} for workflow {workflow_id}") from e

    def _run_agent1_architecture_with_feedback(self, workflow_id: str, requirements: str, feedback: str):
        """Run Agent 1: Architecture Design with rejection feedback"""
        artifacts_dir = self.workspace / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        print("")
        print("🏗️  Regenerating system architecture with feedback...")
        print("🤖 Agent 1 (Architecture) is incorporating your feedback...")
        print(f"📝 Feedback: {feedback}")
        print("")
        sys.stdout.flush()

        try:
            cmd = [
                self.bash_executable,
                self._convert_path_for_bash(str(self.agents_dir / "agent1_architecture.sh")),
                "--requirements-path", self._convert_path_for_bash(requirements),
                "--workspace-root", self._convert_path_for_bash(str(self.workspace)),
                "--output-dir", self._convert_path_for_bash(str(artifacts_dir)),
                "--feedback", feedback  # Pass feedback to the agent
            ]

            subprocess.run(cmd, check=True, timeout=self.config.timeout_seconds)
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Agent 1 (Architecture) timed out after {self.config.timeout_seconds}s for workflow {workflow_id}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Agent 1 (Architecture) failed with exit code {e.returncode} for workflow {workflow_id}") from e

    def _run_agent2_task_planning(self, workflow_id: str, requirements: str) -> List[Dict]:
        """Run Agent 2: Task Planner"""
        artifacts_dir = self.workspace / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        print("")
        print(f"🔍 Analyzing architecture and requirements...")
        print("🤖 Agent 2 (Task Planner) is working...")
        print(f"⏳ Planning tasks...")
        print("")
        sys.stdout.flush()

        # Run without capturing output so we see real-time progress
        subprocess.run([
            self.bash_executable,
            self._convert_path_for_bash(str(self.agents_dir / "agent2_task_planner.sh")),
            "--requirements-path", self._convert_path_for_bash(requirements),
            "--workspace-root", self._convert_path_for_bash(str(self.workspace)),
            "--output-dir", self._convert_path_for_bash(str(artifacts_dir))
        ], check=True, timeout=self.config.timeout_seconds)

        # Parse and validate tasks.json
        tasks_file = artifacts_dir / "tasks.json"
        try:
            with open(tasks_file) as f:
                tasks_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in tasks.json: {e}")

        # Validate structure
        validation_errors = self._validate_tasks_json(tasks_data)
        if validation_errors:
            error_msg = "tasks.json validation failed:\n" + "\n".join(f"  - {e}" for e in validation_errors)
            raise ValueError(error_msg)

        tasks = tasks_data.get('tasks', [])
        if not tasks:
            print("⚠️  Warning: No tasks found in tasks.json")

        return tasks
    
    def _run_agent3_setup(self, workflow_id: str, requirements: str):
        """Run Agent 3: Setup Phase"""
        print("")
        print("🔧 Setting up development environment based on architecture...")
        print("🤖 Agent 3 (Setup) is configuring tools and dependencies...")
        print("")
        sys.stdout.flush()

        subprocess.run([
            self.bash_executable,
            self._convert_path_for_bash(str(self.agents_dir / "agent3_setup_impl.sh")),
            "--workspace-root", self._convert_path_for_bash(str(self.workspace)),
            "--requirements", self._convert_path_for_bash(requirements),
            "--mode", "setup"
        ], check=True, timeout=self.config.timeout_seconds)

    def _run_agent3_implement(self, workflow_id: str, task_id: str, requirements: str):
        """Run Agent 3: Implementation Phase"""
        tasks_file = self.workspace / "artifacts" / "tasks.json"

        sys.stdout.flush()

        subprocess.run([
            self.bash_executable,
            self._convert_path_for_bash(str(self.agents_dir / "agent3_setup_impl.sh")),
            "--workspace-root", self._convert_path_for_bash(str(self.workspace)),
            "--task-id", task_id,
            "--task-file", self._convert_path_for_bash(str(tasks_file)),
            "--requirements", self._convert_path_for_bash(requirements),
            "--mode", "implement"
        ], check=True, timeout=self.config.timeout_seconds)

    def _run_agent4_testing(self, workflow_id: str, task_id: str):
        """Run Agent 4: Testing"""
        tasks_file = self.workspace / "artifacts" / "tasks.json"

        sys.stdout.flush()

        # Build command with GitHub parameters if enabled
        cmd = [
            self.bash_executable,
            self._convert_path_for_bash(str(self.agents_dir / "agent4_testing.sh")),
            "--workspace-root", self._convert_path_for_bash(str(self.workspace)),
            "--task-id", task_id,
            "--task-file", self._convert_path_for_bash(str(tasks_file)),
            "--max-retries", str(self.config.max_retries),
            "--test-timeout", str(self.config.test_timeout),
            "--fix-timeout", str(self.config.fix_timeout),
            "--smart-retry", "true" if self.config.smart_retry else "false"
        ]

        # Add GitHub parameters
        cmd.extend([
            "--github-enabled", "true" if self.config.github_enabled else "false",
            "--github-auto-commit", "true" if self.config.github_auto_commit else "false",
            "--github-repo-url", self.config.github_repository_url,
            "--github-branch", self.config.github_branch,
            "--github-commit-prefix", self.config.github_commit_message_prefix,
            "--github-user-name", self.config.github_user_name,
            "--github-user-email", self.config.github_user_email
        ])

        subprocess.run(cmd, check=True, timeout=self.config.timeout_seconds)

    def _git_commit_task(self, task_id: str, task_title: str):
        """Commit task changes to git repository"""
        if not self.config.github_enabled:
            print("  ℹ️  GitHub integration disabled - skipping commit")
            return

        print(f"  📦 Committing to git... (branch: {self.config.github_branch})")

        try:
            # Source git helper functions
            git_helper = self.agents_dir / "common" / "git_helper.sh"

            # Build commit message
            commit_msg_prefix = self.config.github_commit_message_prefix or "[AI-Generated]"

            # Call git_commit_and_push function
            cmd = [
                self.bash_executable,
                "-c",
                f"""
                source "{git_helper}"
                git_commit_and_push \\
                    "{self.project_code_dir}" \\
                    "{commit_msg_prefix}" \\
                    "{task_title}" \\
                    "{task_id}" \\
                    "{self.config.github_repository_url}" \\
                    "{self.config.github_branch}" \\
                    "{self.config.github_user_name}" \\
                    "{self.config.github_user_email}"
                """
            ]

            result = subprocess.run(
                cmd,
                capture_output=False,  # Show git output in real-time
                text=True,
                timeout=300  # 5 minutes for git operations
            )

            print()  # Add newline after git output
            if result.returncode == 0:
                if self.config.github_auto_commit and self.config.github_repository_url:
                    print(f"  ✓ Committed and pushed to GitHub (branch: {self.config.github_branch})")
                    print(f"     Task: {task_id}")
                else:
                    print(f"  ✓ Committed locally (branch: {self.config.github_branch})")
                    print(f"     Task: {task_id}")
            else:
                print(f"  ⚠️  Git commit failed with exit code: {result.returncode}")
                print(f"     Task {task_id} completed but not committed to git")
                print(f"     You may need to commit manually")
                # Don't fail the workflow on git errors

        except subprocess.TimeoutExpired:
            print("  ⚠️  Git operation timed out (limit: 5 minutes)")
            print(f"     Task {task_id} completed but not committed to git")
        except Exception as e:
            print(f"  ⚠️  Git error: {e}")
            print(f"     Task {task_id} completed but not committed to git")

    def _update_tasks_md(self, task_id: str):
        """Update tasks.md and tasks.json to mark task as complete"""
        try:
            from datetime import datetime, timezone

            tasks_md_file = self.workspace / "artifacts" / "tasks.md"

            if not tasks_md_file.exists():
                print(f"  ⚠️  tasks.md not found, skipping update")
                return

            # Generate ISO 8601 timestamp
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            # Call the tasks_md_updater script with timestamp
            updater_script = self.agents_dir / "common" / "tasks_md_updater.sh"

            result = subprocess.run(
                [self.bash_executable, str(updater_script), str(tasks_md_file), task_id, timestamp],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                # Parse output to show what was updated
                if "tasks.json" in result.stdout:
                    print(f"  ✓ Updated tasks.md and tasks.json")
                else:
                    print(f"  ✓ Updated tasks.md")

                # Show the output for debugging
                for line in result.stdout.strip().split('\n'):
                    if line.startswith('✓'):
                        print(f"    {line}")
            else:
                print(f"  ⚠️  Could not update task files: {result.stderr}")

        except Exception as e:
            print(f"  ⚠️  Error updating task files: {e}")

    def _run_agent5_documentation(self, workflow_id: str, task_id: str):
        """Run Agent 5: Documentation"""
        tasks_file = self.workspace / "artifacts" / "tasks.json"

        sys.stdout.flush()

        subprocess.run([
            self.bash_executable,
            str(self.agents_dir / "agent5_documentation.sh"),
            "--workspace-root", str(self.workspace),
            "--task-id", task_id,
            "--task-file", str(tasks_file)
        ], check=True, timeout=self.config.timeout_seconds)


