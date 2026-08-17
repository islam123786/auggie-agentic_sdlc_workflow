# 🤖 AI Project Automation Orchestrator

**Transform project requirements into complete, tested, and documented code automatically using AI agents.**

> A Python-based orchestration system that uses 5 AI agents to analyze requirements, design architecture, break down tasks, implement features, run tests, and generate documentation - all automatically.

## 📑 Table of Contents

- [What This Does](#-what-this-does)
- [Quick Start](#-quick-start)
- [What You Get](#-what-you-get)
- [The 5 Agents](#-the-5-agents)
- [CLI Commands](#-cli-commands)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 What This Does

**Input:** Markdown requirements file (Business Requirements Document)
**Output:** Complete project with code, tests, and documentation

### The 5-Agent Workflow

1. **Agent 1 (Architecture Designer):** Analyzes requirements → Designs system architecture & selects tech stack → **⏸️ Pauses for user approval**
2. **Agent 2 (Task Planner):** Uses requirements + approved architecture → Creates detailed task breakdown
3. **Agent 3 (Setup & Implementation):** Sets up environment → Implements each task sequentially
4. **Agent 4 (Testing):** Creates test plans → Runs tests → Auto-fixes failures (smart retry with timeout limits)
5. **Agent 5 (Documentation):** Generates design documentation with Mermaid diagrams for each task

**Key Principle:** Architecture approval required before implementation begins - you control the tech stack.

### ✨ Key Features

- ✅ **Architecture-First Workflow:** Review and approve system design before any code is written
- ✅ **Docker + Open-Source Stack:** PostgreSQL, Redis, RabbitMQ, MinIO - portable and cloud-ready
- ✅ **Smart Auto-Testing:** Tests retry with intelligent timeout management
- ✅ **Complete Output:** Working code + comprehensive tests + detailed documentation
- ✅ **State Management:** SQLite-based tracking for workflow reliability
- ✅ **GitHub Integration:** Optional auto-commit after successful tests
- ✅ **Resume Capability:** Continue interrupted workflows from last successful phase

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **auggie CLI** ([Augment Code](https://www.augmentcode.com/) - must be authenticated)
- **jq** (JSON processor)
- **Bash** (Git Bash on Windows, native on macOS/Linux)

### Installation

```bash
# 1. Clone repository
git clone <your-repo-url>
cd auggie-agentic_sdlc_workflow

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate          # macOS/Linux
# or: .\venv\Scripts\Activate.ps1  # Windows PowerShell

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install system dependencies
brew install jq              # macOS
sudo apt-get install jq      # Ubuntu/Debian
# Windows: Download from https://jqlang.github.io/jq/download/

# 5. Install and authenticate auggie CLI
# Follow official guide: https://docs.augmentcode.com/
auggie login
```

### Run Your First Workflow

```bash
# Always activate virtual environment first
source venv/bin/activate  # macOS/Linux

# Start workflow (basic - no GitHub)
python3 -m orchestrator.cli run \
  --requirements ./examples/sample-requirements.md \
  --workspace ./workspace

# OR start with GitHub integration (auto-commit after each task)
python3 -m orchestrator.cli run \
  --requirements ./examples/sample-requirements.md \
  --workspace ./workspace \
  --github-repo https://github.com/your-username/your-repo.git

python3 -m orchestrator.cli run \
  --requirements /mnt/d/workspace/QCells_Chat_Application/requirements/ChatApplicationBRD.md \
  --workspace /mnt/d/workspace/QCells_Chat_Application \
  --github-repo https://github.com/mohammed-siddiqui-ml/QCells_Chat_Application.git 
# Agent 1 will pause for architecture approval
# Review: workspace/artifacts/architecture.md
# Then approve:
python3 -m orchestrator.cli approve <workflow-id> --workspace ./workspace

# OR approve with GitHub (if you didn't enable it initially)
python3 -m orchestrator.cli approve <workflow-id> \
  --workspace ./workspace \
  --github-repo https://github.com/your-username/your-repo.git

# Agents 2-5 run automatically after approval
# Your complete project: workspace/project-code/
```

### Typical Workflow

1. **Run command** → Agent 1 creates `architecture.md`
2. **⏸️ Workflow pauses** → Review architecture design
3. **Approve** → Run `approve` command with workflow ID
4. **Automatic execution** → Agents 2-5 complete the project
5. **Done** → Find working project in `workspace/project-code/`

---

## 📁 What You Get

After running, your workspace contains:

```
workspace/
├── .state.db                          # SQLite database for workflow state tracking
│
├── project-code/                      # 🎯 YOUR GENERATED PROJECT
│   ├── src/                          # Source code (structure from architecture)
│   ├── tests/                        # Comprehensive test suites
│   ├── requirements.txt              # Dependencies (or package.json, etc.)
│   ├── README.md                     # Project documentation
│   ├── docker-compose.yml            # Docker orchestration
│   └── .git/                         # Git repo (if GitHub integration enabled)
│
└── artifacts/                         # 📚 WORKFLOW ARTIFACTS & LOGS
    ├── architecture.md               # ⭐ System architecture & tech stack (Agent 1)
    ├── tasks.md                      # Human-readable task breakdown (Agent 2)
    ├── tasks.json                    # Machine-readable task list (Agent 2)
    │
    ├── setup/
    │   └── setup-log.md              # Environment setup log (Agent 3)
    │
    └── tasks/
        ├── task-001/
        │   ├── implementation.md           # Implementation details (Agent 3)
        │   ├── testing.md                  # Test plan + results + fixes (Agent 4)
        │   └── documentation.md            # Design docs with diagrams (Agent 5)
        │
        ├── task-002/
        │   ├── implementation.md
        │   ├── testing.md
        │   └── documentation.md
        │
        └── ...
```

**What you get:**
- ✅ **Working project** in `project-code/` with Docker support
- ✅ **Architecture document** you reviewed and approved
- ✅ **Test suites** with consolidated test results (plan + execution + fixes in one file)
- ✅ **Design documentation** for each task with Mermaid diagrams
- ✅ **Complete audit trail** - 3 markdown files per task (down from ~9 files)

---

## 🤖 The 5 Agents

### Agent 1: Architecture Designer 🏗️

**Runs:** Once at workflow start
**Input:** Requirements document (`.md` file)
**Output:** `workspace/artifacts/architecture.md`

**What it does:**
- Analyzes business requirements
- Selects technology stack (Docker + open-source: PostgreSQL, Redis, RabbitMQ, MinIO)
- Designs system architecture with component breakdown
- Plans security, scalability, and deployment
- Creates comprehensive architecture document

**⏸️ User Action Required:** Review and approve before implementation begins

**Script:** `agents/agent1_architecture.sh`

---

### Agent 2: Task Planner 📋

**Runs:** Once after architecture approval
**Input:** Requirements + approved architecture
**Output:** `workspace/artifacts/tasks.md` and `tasks.json`

**What it does:**
- Breaks project into actionable tasks
- Sequences tasks with dependencies
- Categorizes tasks (setup, infrastructure, implementation, integration, testing, documentation)
- Creates human-readable and machine-readable formats

**Script:** `agents/agent2_task_planner.sh`

---

### Agent 3: Setup & Implementation ⚙️

**Runs:** Setup once, then once per task
**Input:** Architecture + task details
**Output:** Working code in `workspace/project-code/`

**What it does:**

**Setup mode:**
- Creates project structure per architecture
- Installs dependencies
- Configures tools and frameworks

**Implementation mode (per task):**
- Implements features according to architecture
- Follows best practices
- Creates modular, maintainable code

**Script:** `agents/agent3_setup_impl.sh`

---

### Agent 4: Testing 🧪

**Runs:** Once per task after implementation
**Input:** Task details + implementation code
**Output:** Test files + test results in task artifacts

**What it does:**
- Creates test plan for the task
- Generates test suite
- Executes tests
- Auto-fixes failures (with timeout limits)
- Reruns tests after fixes
- **Optional:** Auto-commits to GitHub on success

**Script:** `agents/agent4_testing.sh`

---

### Agent 5: Documentation 📝

**Runs:** Once per task after testing
**Input:** Task details + implementation + test results
**Output:** `design-doc.md` in task artifacts

**What it does:**
- Generates design documentation
- Creates Mermaid diagrams (architecture, sequence, flow)
- Documents implementation details and API
- Explains design decisions

**Script:** `agents/agent5_documentation.sh`

---

## 🔧 CLI Commands

### Start a Workflow

```bash
# Basic usage
python3 -m orchestrator.cli run \
  --requirements <path/to/requirements.md> \
  --workspace <path/to/workspace>

# With GitHub integration (auto-commit and push after each task)
python3 -m orchestrator.cli run \
  --requirements ./my-project.md \
  --workspace ./workspace \
  --github-repo https://github.com/user/repo.git \
  --github-branch main  # optional, defaults to 'main'
```

### Manage Workflows

```bash
# List all workflows
python3 -m orchestrator.cli list --workspace ./workspace

# Check specific workflow status
python3 -m orchestrator.cli status <workflow-id> --workspace ./workspace

# Approve architecture (required to continue)
python3 -m orchestrator.cli approve <workflow-id> --workspace ./workspace

# Reject architecture with feedback (auto-regenerates with feedback)
python3 -m orchestrator.cli reject <workflow-id> \
  --workspace ./workspace \
  --feedback "Use PostgreSQL instead of MySQL"
# Note: This automatically deletes old architecture.md and regenerates a new one

# Resume a failed or paused workflow (basic)
python3 -m orchestrator.cli resume <workflow-id> \
  --workspace ./workspace

# Resume with GitHub integration (NEW - simplified!)
python3 -m orchestrator.cli resume <workflow-id> \
  --workspace ./workspace \
  --github-repo https://github.com/user/repo.git

# Resume with custom branch
python3 -m orchestrator.cli resume <workflow-id> \
  --workspace ./workspace \
  --github-repo https://github.com/user/repo.git \
  --github-branch develop

# Show version
python3 -m orchestrator.cli version
```

### Resume Interrupted Workflow

**What workflows can be resumed?**
- ✅ Failed workflows (status: `failed`)
- ✅ Paused workflows (status: `paused`)
- ✅ Running workflows (status: `running`)
- ❌ Completed workflows (status: `completed`)

```bash
# Step 1: Check workflow status (auto-loads workflow ID from workspace/.workflow_id)
python3 -m orchestrator.cli status --workspace ./workspace

# Step 2: Resume from where it stopped (auto-loads workflow ID)
python3 -m orchestrator.cli resume --workspace ./workspace

# Step 3: Resume with GitHub integration (auto-commit and push)
python3 -m orchestrator.cli resume \
  --workspace ./workspace \
  --github-repo https://github.com/user/repo.git

# Step 4: Resume with custom branch
python3 -m orchestrator.cli resume \
  --workspace ./workspace \
  --github-repo https://github.com/user/repo.git \
  --github-branch develop

# Alternative: Explicit workflow ID (if needed)
python3 -m orchestrator.cli resume <workflow-id> --workspace ./workspace
```

**How Resume Works:**
- ✅ Skips completed tasks (reads from state database)
- ✅ Continues from last failed/incomplete task
- ✅ Preserves all previous work (architecture, tasks, completed implementations)
- ✅ Can enable GitHub integration even if original run didn't have it
- ✅ **Auto-loads workflow ID** from `workspace/.workflow_id` - no need to remember it!

---

## ⚙️ Configuration

### Default Configuration

The orchestrator uses sensible defaults but can be customized via `config.yaml`:

```yaml
workspace:
  root: "./workspace"
  agents_dir: "./agents"
  state_db: "./workspace/.state.db"

orchestrator:
  max_retries: 3
  timeout_seconds: 3600  # 1 hour

agents:
  policies_dir: "./agents/policies"

github:
  enabled: false               # Set to true to enable auto-commit
  auto_commit: false           # Auto-commit after successful tests
  auto_push: false             # Auto-push to remote
  repository_url: ""           # e.g., https://github.com/user/repo.git
  branch: "main"
  commit_message_prefix: "[AI-Generated]"
  git_user_name: ""            # Optional, uses system config if empty
  git_user_email: ""           # Optional, uses system config if empty
```

### GitHub Integration

Enable automatic commits after successful tests:

1. **Edit `config.yaml`:**
   ```yaml
   github:
     enabled: true
     auto_commit: true
     auto_push: true  # Optional: push to remote
     repository_url: "https://github.com/user/repo.git"
     branch: "main"
   ```

2. **Ensure git credentials are configured:**
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

3. **Run workflow:**
   - After each task's tests pass, Agent 4 auto-commits the code
   - Commit message: `[AI-Generated] Implemented: <task-title>`

**Alternative:** Use CLI flags (overrides config.yaml):
```bash
python3 -m orchestrator.cli run \
  --requirements ./req.md \
  --workspace ./workspace \
  --github-repo https://github.com/user/repo.git
# Just providing --github-repo automatically enables commit and push!
```

---

## ⚠️ Important Notes

### Before Running

1. **Always activate virtual environment:**
   ```bash
   source venv/bin/activate  # macOS/Linux
   ```

2. **Architecture approval is required:**
   - Workflow pauses after Agent 1 creates `architecture.md`
   - Review tech stack and design decisions
   - Must run `approve` command to continue

3. **Requirements format:**
   - Must be markdown (`.md`) file
   - Be specific about features and constraints
   - No need to specify technical details (Agent 1 handles that)

### During Execution

4. **Be patient:**
   - Each agent takes 5-15 minutes (complexity dependent)
   - Silent periods are normal during AI processing
   - Check `workspace/artifacts/` for real-time progress

5. **Workflow state:**
   - All state saved in `workspace/.state.db` (SQLite)
   - Check status: `python3 -m orchestrator.cli list --workspace ./workspace`
   - Can resume interrupted workflows with `--resume` flag

### After Completion

6. **Review outputs:**
   - Working code: `workspace/project-code/`
   - All artifacts: `workspace/artifacts/`
   - Test results in task-specific folders
   - Architecture document is your reference

7. **GitHub integration:**
   - Optional auto-commit after successful tests
   - Configure in `config.yaml` or use CLI flags
   - Non-fatal: workflow continues if git operations fail

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────┐
│  User: requirements.md                   │
└────────────────┬────────────────────────┘
                 ▼
┌─────────────────────────────────────────┐
│  Python Orchestrator (workflow_engine)  │
│  - State tracking (.state.db)           │
│  - Agent coordination                   │
└────────────────┬────────────────────────┘
                 ▼
        ┌────────┴────────┐
        ▼                 ▼
┌──────────────┐  ┌──────────────┐
│  Agent 1     │  │  Auggie CLI  │
│  Arch Design │  │  (AI Engine) │
└──────┬───────┘  └──────────────┘
       ▼
  ⏸️  PAUSE FOR APPROVAL
       ▼
┌──────────────┐
│  Agent 2     │
│  Task Plan   │
└──────┬───────┘
       ▼
┌──────────────┐
│  Agent 3     │
│  Setup       │
└──────┬───────┘
       ▼
  ┌────────────────┐
  │  For Each Task │
  └────┬───────────┘
       ▼
  ┌────────────────┐
  │  Agent 3: Code │
  │  Agent 4: Test │
  │  Agent 5: Docs │
  └────┬───────────┘
       ▼
┌──────────────────────┐
│  Complete Project    │
│  workspace/          │
│    project-code/     │
│    artifacts/        │
└──────────────────────┘
```

---

## 🐛 Troubleshooting

### Common Issues

**"auggie: command not found"**
```bash
# Install auggie CLI from Augment Code
# Visit: https://docs.augmentcode.com/

# Verify installation
which auggie
auggie --version

# Login
auggie login
```

**"Permission denied" on shell scripts**
```bash
chmod +x agents/*.sh
```

**"bash: command not found" (Windows)**
- Install Git for Windows (includes Git Bash)
- Or use WSL (Windows Subsystem for Linux)
- The orchestrator auto-detects bash executable

**Virtual environment not activated**
```bash
# Always activate before running
source venv/bin/activate          # macOS/Linux
.\venv\Scripts\Activate.ps1       # Windows PowerShell
```

**Workflow stuck at architecture approval**
```bash
# List workflows to find the workflow ID
python3 -m orchestrator.cli list --workspace ./workspace

# Approve with the workflow ID
python3 -m orchestrator.cli approve <workflow-id> --workspace ./workspace
```

**Tests failing**
- Review: `workspace/artifacts/tasks/<task-id>/test-results-*.md`
- Agent 4 auto-retries with timeout limits
- Manually fix code in `workspace/project-code/` if needed
- Re-run with `--resume` flag to continue

**"No module named 'orchestrator'"**
```bash
# Make sure you're in the project root directory
pwd  # Should show .../auggie-agentic_sdlc_workflow

# And virtual environment is activated
which python  # Should show venv/bin/python
```

**Workflow database errors**
- The `.state.db` file tracks workflow state
- Located at: `workspace/.state.db`
- If corrupted, delete it to start fresh (loses workflow history)

---

## � Command Reference (Quick Reference)

### Starting Workflows

```bash
# Basic workflow (no GitHub)
python3 -m orchestrator.cli run -r requirements.md -w ./workspace

# With GitHub (auto-commit and push after each task)
python3 -m orchestrator.cli run -r requirements.md -w ./workspace \
  --github-repo https://github.com/user/repo.git

# Custom branch
python3 -m orchestrator.cli run -r requirements.md -w ./workspace \
  --github-repo https://github.com/user/repo.git --github-branch develop
```

### Managing Workflows

```bash
# List all workflows
python3 -m orchestrator.cli list -w ./workspace

# Check workflow status
python3 -m orchestrator.cli status <workflow-id> -w ./workspace

# Approve architecture
python3 -m orchestrator.cli approve <workflow-id> -w ./workspace

# Approve with GitHub
python3 -m orchestrator.cli approve <workflow-id> -w ./workspace \
  --github-repo https://github.com/user/repo.git

# Reject architecture with feedback
python3 -m orchestrator.cli reject <workflow-id> -w ./workspace \
  --feedback "Your feedback here"
```

### Resuming Workflows

```bash
# Resume basic (auto-loads workflow ID from workspace/.workflow_id)
python3 -m orchestrator.cli resume -w ./workspace

# Resume with explicit workflow ID
python3 -m orchestrator.cli resume <workflow-id> -w ./workspace

# Resume with GitHub (auto-loads workflow ID)
python3 -m orchestrator.cli resume -w ./workspace \
  --github-repo https://github.com/user/repo.git

# Resume with custom branch
python3 -m orchestrator.cli resume -w ./workspace \
  --github-repo https://github.com/user/repo.git --github-branch develop
```

**💡 Auto-Loading Workflow ID:**
- Workflow ID is automatically saved to `workspace/.workflow_id` file
- All commands (`resume`, `approve`, `reject`, `status`) can auto-load it
- No need to copy/paste workflow IDs anymore!
```bash
# These commands work without specifying workflow ID:
python3 -m orchestrator.cli resume -w ./workspace
python3 -m orchestrator.cli status -w ./workspace
python3 -m orchestrator.cli approve -w ./workspace
python3 -m orchestrator.cli reject -w ./workspace -f "feedback"
```

### Key Points

- ✅ **Just provide `--github-repo`** - No need for `--github-enable` or `--github-push`
- ✅ **GitHub auto-enabled** - Providing the repo URL automatically enables commit and push
- ✅ **Default branch is `main`** - Use `--github-branch` to change it
- ✅ **Works for all commands** - `run`, `resume`, and `approve`

---

## �📚 Documentation

- **[Example Requirements](examples/sample-requirements.md)** - Sample BRD to get started
- **[Agent Policies](agents/policies/)** - Detailed guidelines for each agent
- **[Configuration](#configuration)** - config.yaml options

---

## 📄 License

MIT License - See LICENSE file for details

---

**Ready to automate your project? Start with a clear requirements document!** 🚀