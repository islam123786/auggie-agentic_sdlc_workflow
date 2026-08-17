"""
Project Automation Orchestrator

A Python-based orchestration system for automated project development
using AI agents.
"""

__version__ = "1.0.0"
__author__ = "Project Automation Team"

from .workflow_engine import WorkflowEngine
from .config import Config

__all__ = ["WorkflowEngine", "Config"]
