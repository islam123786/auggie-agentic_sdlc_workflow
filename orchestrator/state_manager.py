"""
State management for workflow tracking
"""
import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from contextlib import contextmanager


class StateManager:
    """Manages workflow state with SQLite persistence"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize the database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Workflows table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY,
                    requirements_path TEXT NOT NULL,
                    status TEXT CHECK(status IN ('running', 'paused', 'failed', 'completed')),
                    current_phase TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    github_enabled INTEGER DEFAULT 0,
                    github_auto_commit INTEGER DEFAULT 0,
                    github_repository_url TEXT,
                    github_branch TEXT
                )
            """)

            # Phases table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS phases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    phase_name TEXT NOT NULL,
                    status TEXT,
                    data JSON,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (workflow_id) REFERENCES workflows(id)
                )
            """)

            # Tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    task_id TEXT NOT NULL UNIQUE,
                    task_title TEXT,
                    status TEXT CHECK(status IN ('running', 'completed', 'failed')),
                    current_phase TEXT CHECK(current_phase IN ('implementation', 'testing', 'documentation', 'completed')),
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    failed_at TIMESTAMP,
                    error_message TEXT,
                    FOREIGN KEY (workflow_id) REFERENCES workflows(id)
                )
            """)
    
    def create_workflow(self, requirements_path: str, github_enabled: bool = False,
                        github_auto_commit: bool = False, github_repository_url: str = None,
                        github_branch: str = 'main') -> str:
        """Create a new workflow with GitHub configuration"""
        workflow_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO workflows (id, requirements_path, status, current_phase, created_at, updated_at,
                                       github_enabled, github_auto_commit, github_repository_url, github_branch)
                VALUES (?, ?, 'running', 'initialization', ?, ?, ?, ?, ?, ?)
            """, (workflow_id, requirements_path, now, now,
                  1 if github_enabled else 0,
                  1 if github_auto_commit else 0,
                  github_repository_url,
                  github_branch))

        return workflow_id
    
    def update_phase(self, workflow_id: str, phase_name: str, data: Dict):
        """Update current phase"""
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Update workflow
            cursor.execute("""
                UPDATE workflows
                SET current_phase = ?, updated_at = ?
                WHERE id = ?
            """, (phase_name, now, workflow_id))

            # Insert phase record
            cursor.execute("""
                INSERT INTO phases (workflow_id, phase_name, status, data, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (workflow_id, phase_name, data.get('status', 'running'),
                  json.dumps(data), now, now if data.get('status') == 'completed' else None))
    
    def resume_workflow(self, workflow_id: str):
        """Resume a failed or paused workflow"""
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE workflows
                SET status = 'running', updated_at = ?
                WHERE id = ? AND status IN ('failed', 'paused')
            """, (now, workflow_id))

            if cursor.rowcount == 0:
                raise ValueError(f"Cannot resume workflow {workflow_id} - not in failed/paused state")

    def get_last_completed_phase(self, workflow_id: str) -> Optional[str]:
        """Get the last successfully completed phase"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT phase_name FROM phases
                WHERE workflow_id = ? AND status = 'completed'
                ORDER BY completed_at DESC
                LIMIT 1
            """, (workflow_id,))
            row = cursor.fetchone()
            return row['phase_name'] if row else None

    def get_completed_tasks(self, workflow_id: str) -> List[str]:
        """Get list of completed task IDs"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT task_id FROM tasks
                WHERE workflow_id = ? AND status = 'completed'
                ORDER BY started_at
            """, (workflow_id,))
            return [row[0] for row in cursor.fetchall()]

    def get_task_status(self, workflow_id: str, task_id: str) -> Optional[Dict]:
        """Get detailed status of a specific task"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT task_id, task_title, status, current_phase, started_at, completed_at, failed_at, error_message
                FROM tasks
                WHERE workflow_id = ? AND task_id = ?
            """, (workflow_id, task_id))
            row = cursor.fetchone()

        return dict(row) if row else None

    def get_last_failed_task(self, workflow_id: str) -> Optional[Dict]:
        """Get the most recent failed task with details"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT task_id, task_title, status, current_phase, failed_at, error_message
                FROM tasks
                WHERE workflow_id = ? AND status = 'failed'
                ORDER BY failed_at DESC
                LIMIT 1
            """, (workflow_id,))
            row = cursor.fetchone()

        return dict(row) if row else None

    def get_all_tasks_status(self, workflow_id: str) -> List[Dict]:
        """Get status of all tasks for a workflow"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT task_id, task_title, status, current_phase, started_at, completed_at, failed_at, error_message
                FROM tasks
                WHERE workflow_id = ?
                ORDER BY started_at ASC
            """, (workflow_id,))
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def start_task(self, workflow_id: str, task_id: str, task_title: str, preserve_phase: bool = False):
        """Start a new task and mark it as running

        Args:
            workflow_id: The workflow ID
            task_id: The task ID
            task_title: The task title
            preserve_phase: If True, keeps existing phase when updating (for resume). If False, resets to 'implementation'
        """
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Check if task already exists
            cursor.execute("""
                SELECT id, current_phase FROM tasks WHERE task_id = ?
            """, (task_id,))
            existing = cursor.fetchone()

            if existing:
                # Update existing task
                if preserve_phase:
                    # Keep the current phase (for resume)
                    cursor.execute("""
                        UPDATE tasks
                        SET status = 'running',
                            completed_at = NULL,
                            failed_at = NULL,
                            error_message = NULL
                        WHERE task_id = ?
                    """, (task_id,))
                else:
                    # Reset to implementation phase (fresh start)
                    cursor.execute("""
                        UPDATE tasks
                        SET status = 'running',
                            current_phase = 'implementation',
                            started_at = ?,
                            completed_at = NULL,
                            failed_at = NULL,
                            error_message = NULL
                        WHERE task_id = ?
                    """, (now, task_id))
            else:
                # Insert new task
                cursor.execute("""
                    INSERT INTO tasks (workflow_id, task_id, task_title, status, current_phase, started_at)
                    VALUES (?, ?, ?, 'running', 'implementation', ?)
                """, (workflow_id, task_id, task_title, now))

    def update_task_phase(self, workflow_id: str, task_id: str, phase: str):
        """Update current phase of a task (implementation -> testing -> documentation)"""
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tasks
                SET current_phase = ?
                WHERE task_id = ? AND workflow_id = ?
            """, (phase, task_id, workflow_id))

    def complete_task(self, workflow_id: str, task_id: str):
        """Mark task as completed"""
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tasks
                SET status = 'completed',
                    current_phase = 'completed',
                    completed_at = ?
                WHERE task_id = ? AND workflow_id = ?
            """, (now, task_id, workflow_id))

    def fail_task(self, workflow_id: str, task_id: str, phase: str, error_message: str):
        """Mark task as failed with error details"""
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tasks
                SET status = 'failed',
                    current_phase = ?,
                    failed_at = ?,
                    error_message = ?
                WHERE task_id = ? AND workflow_id = ?
            """, (phase, now, error_message, task_id, workflow_id))

    def update_task(self, workflow_id: str, task_id: str, status: str):
        """Legacy method for backward compatibility - use start_task, complete_task, or fail_task instead"""
        if status == 'completed':
            self.complete_task(workflow_id, task_id)
        else:
            # For other statuses, just update
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE tasks
                    SET status = ?
                    WHERE task_id = ? AND workflow_id = ?
                """, (status, task_id, workflow_id))
    
    def mark_completed(self, workflow_id: str):
        """Mark workflow as completed"""
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE workflows
                SET status = 'completed', completed_at = ?, updated_at = ?
                WHERE id = ?
            """, (now, now, workflow_id))

    def mark_failed(self, workflow_id: str, error: str):
        """Mark workflow as failed"""
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE workflows
                SET status = 'failed', updated_at = ?
                WHERE id = ?
            """, (now, workflow_id))

            # Log error in phases
            cursor.execute("""
                INSERT INTO phases (workflow_id, phase_name, status, data, started_at, completed_at)
                VALUES (?, 'error', 'failed', ?, ?, ?)
            """, (workflow_id, json.dumps({'error': error}), now, now))

    def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        """Get workflow details"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM workflows WHERE id = ?
            """, (workflow_id,))
            row = cursor.fetchone()

        return dict(row) if row else None

    def list_workflows(self, limit: int = 10) -> List[Dict]:
        """List recent workflows"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM workflows
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_architecture_status(self, workflow_id: str) -> bool:
        """Check if architecture has been approved for this workflow"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status FROM phases
                WHERE workflow_id = ? AND phase_name = 'architecture'
                ORDER BY completed_at DESC
                LIMIT 1
            """, (workflow_id,))
            row = cursor.fetchone()

        return row and row[0] == 'approved'

    def approve_architecture(self, workflow_id: str):
        """Mark architecture as approved"""
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE phases
                SET status = 'approved', completed_at = ?
                WHERE workflow_id = ? AND phase_name = 'architecture'
            """, (now, workflow_id))

    def reject_architecture(self, workflow_id: str, feedback: str):
        """Mark architecture as rejected with feedback"""
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE phases
                SET status = 'rejected',
                    data = ?,
                    completed_at = ?
                WHERE workflow_id = ? AND phase_name = 'architecture'
            """, (json.dumps({'feedback': feedback}), now, workflow_id))

    def get_architecture_regeneration_count(self, workflow_id: str) -> int:
        """Get the number of times architecture has been regenerated"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM phases
                WHERE workflow_id = ? AND phase_name = 'architecture' AND status = 'rejected'
            """, (workflow_id,))
            row = cursor.fetchone()
            return row[0] if row else 0

    def get_architecture_feedback(self, workflow_id: str) -> Optional[str]:
        """Get the most recent architecture rejection feedback"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT data FROM phases
                WHERE workflow_id = ? AND phase_name = 'architecture' AND status = 'rejected'
                ORDER BY completed_at DESC
                LIMIT 1
            """, (workflow_id,))
            row = cursor.fetchone()

            if row:
                data = json.loads(row['data'])
                return data.get('feedback')
            return None
