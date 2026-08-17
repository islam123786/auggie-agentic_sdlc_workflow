"""
Configuration management for the orchestrator
"""
import yaml
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Config:
    """Configuration for the workflow orchestrator"""

    workspace_root: str = "./workspace"
    agents_dir: str = "./agents"
    state_db_path: str = "./workspace/.state.db"
    max_retries: int = 2
    timeout_seconds: int = 3600

    # Agent-specific settings
    agent_policies_dir: str = "./agents/policies"

    # Testing agent settings
    test_timeout: int = 600       # 10 minutes for test execution
    fix_timeout: int = 300        # 5 minutes for fix execution
    smart_retry: bool = True      # Skip retry if identical error

    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None

    # GitHub Integration
    github_enabled: bool = False
    github_auto_commit: bool = False
    github_repository_url: str = ""
    github_branch: str = "main"
    github_commit_message_prefix: str = "[AI-Generated]"
    github_user_name: str = ""
    github_user_email: str = ""
    
    def validate(self):
        """Validate configuration values"""
        errors = []

        # Validate numeric ranges
        if self.max_retries < 0:
            errors.append(f"max_retries must be >= 0, got {self.max_retries}")
        if self.max_retries > 10:
            errors.append(f"max_retries should be <= 10 for practical reasons, got {self.max_retries}")

        if self.timeout_seconds < 60:
            errors.append(f"timeout_seconds must be >= 60, got {self.timeout_seconds}")
        if self.timeout_seconds > 86400:  # 24 hours
            errors.append(f"timeout_seconds should be <= 86400 (24h), got {self.timeout_seconds}")

        if self.test_timeout < 30:
            errors.append(f"test_timeout must be >= 30, got {self.test_timeout}")
        if self.test_timeout > 3600:  # 1 hour
            errors.append(f"test_timeout should be <= 3600 (1h), got {self.test_timeout}")

        if self.fix_timeout < 30:
            errors.append(f"fix_timeout must be >= 30, got {self.fix_timeout}")
        if self.fix_timeout > 1800:  # 30 minutes
            errors.append(f"fix_timeout should be <= 1800 (30m), got {self.fix_timeout}")

        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level.upper() not in valid_log_levels:
            errors.append(f"log_level must be one of {valid_log_levels}, got {self.log_level}")

        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    @classmethod
    def from_file(cls, config_path: str) -> 'Config':
        """Load configuration from YAML file"""
        config_file = Path(config_path)

        if not config_file.exists():
            # Return default config if file doesn't exist
            config = cls()
            config.validate()
            return config

        with open(config_file, 'r') as f:
            data = yaml.safe_load(f)

        # Extract relevant fields
        config_data = {}
        if 'workspace' in data:
            config_data['workspace_root'] = data['workspace'].get('root', cls.workspace_root)
            config_data['agents_dir'] = data['workspace'].get('agents_dir', cls.agents_dir)
            config_data['state_db_path'] = data['workspace'].get('state_db', cls.state_db_path)

        if 'orchestrator' in data:
            config_data['max_retries'] = data['orchestrator'].get('max_retries', cls.max_retries)
            config_data['timeout_seconds'] = data['orchestrator'].get('timeout_seconds', cls.timeout_seconds)

        # Testing agent settings
        if 'agents' in data and 'testing' in data['agents']:
            testing_config = data['agents']['testing']
            config_data['test_timeout'] = testing_config.get('test_timeout', cls.test_timeout)
            config_data['fix_timeout'] = testing_config.get('fix_timeout', cls.fix_timeout)
            config_data['smart_retry'] = testing_config.get('smart_retry', cls.smart_retry)

        if 'logging' in data:
            config_data['log_level'] = data['logging'].get('level', cls.log_level)
            config_data['log_file'] = data['logging'].get('file')

        # GitHub integration settings
        if 'github' in data:
            github_config = data['github']
            config_data['github_enabled'] = github_config.get('enabled', cls.github_enabled)
            config_data['github_auto_commit'] = github_config.get('auto_commit', cls.github_auto_commit)
            config_data['github_repository_url'] = github_config.get('repository_url', cls.github_repository_url)
            config_data['github_branch'] = github_config.get('branch', cls.github_branch)
            config_data['github_commit_message_prefix'] = github_config.get('commit_message_prefix', cls.github_commit_message_prefix)
            config_data['github_user_name'] = github_config.get('git_user_name', cls.github_user_name)
            config_data['github_user_email'] = github_config.get('git_user_email', cls.github_user_email)

        config = cls(**config_data)
        config.validate()  # Validate after loading
        return config
    
    def to_dict(self) -> dict:
        """Convert config to dictionary"""
        return {
            'workspace': {
                'root': self.workspace_root,
                'agents_dir': self.agents_dir,
                'state_db': self.state_db_path
            },
            'orchestrator': {
                'max_retries': self.max_retries,
                'timeout_seconds': self.timeout_seconds
            },
            'agents': {
                'testing': {
                    'test_timeout': self.test_timeout,
                    'fix_timeout': self.fix_timeout,
                    'smart_retry': self.smart_retry
                }
            },
            'logging': {
                'level': self.log_level,
                'file': self.log_file
            },
            'github': {
                'enabled': self.github_enabled,
                'auto_commit': self.github_auto_commit,
                'repository_url': self.github_repository_url,
                'branch': self.github_branch,
                'commit_message_prefix': self.github_commit_message_prefix,
                'git_user_name': self.github_user_name,
                'git_user_email': self.github_user_email
            }
        }
    
    def save(self, config_path: str):
        """Save configuration to YAML file"""
        with open(config_path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)
