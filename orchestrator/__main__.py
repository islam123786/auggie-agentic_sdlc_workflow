"""
Main entry point for the orchestrator module
Allows running as: python -m orchestrator.cli
"""
from .cli import cli

if __name__ == '__main__':
    cli()
