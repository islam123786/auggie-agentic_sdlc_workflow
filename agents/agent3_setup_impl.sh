#!/bin/bash

# Agent 3: Setup & Implementation
# Phase 1: Configure development environment (one-time) based on architecture
# Phase 2: Implement each task sequentially

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source environment variables if exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"
fi

# Default values
WORKSPACE_ROOT=""
TASK_ID=""
TASK_FILE=""
REQUIREMENTS_PATH=""
POLICY_FILE="$SCRIPT_DIR/policies/setup-implementation.policy.md"
MODE="setup" # setup | implement

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --workspace-root)
            WORKSPACE_ROOT="$2"
            shift 2
            ;;
        --task-id)
            TASK_ID="$2"
            shift 2
            ;;
        --task-file)
            TASK_FILE="$2"
            shift 2
            ;;
        --requirements)
            REQUIREMENTS_PATH="$2"
            shift 2
            ;;
        --mode)
            MODE="$2"
            shift 2
            ;;
        --policy-file)
            POLICY_FILE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validation
if [ -z "$WORKSPACE_ROOT" ]; then
    echo "Error: --workspace-root is required"
    exit 1
fi

if [ -z "$REQUIREMENTS_PATH" ] || [ ! -f "$REQUIREMENTS_PATH" ]; then
    echo "Error: Valid --requirements file is required"
    exit 1
fi

if [ ! -f "$POLICY_FILE" ]; then
    echo "Error: Policy file not found: $POLICY_FILE"
    exit 1
fi

POLICY_CONTENT=$(cat "$POLICY_FILE")
PROJECT_ROOT="$WORKSPACE_ROOT/project-code"
ARTIFACTS_DIR="$WORKSPACE_ROOT/artifacts"

if [ "$MODE" == "setup" ]; then
    # ========================================================================
    # Phase 1: SETUP MODE
    # ========================================================================
    
    echo "Agent 3: Setup Mode"
    echo "Setting up development environment..."
    echo ""
    
    mkdir -p "$PROJECT_ROOT"
    mkdir -p "$ARTIFACTS_DIR/setup"
    
    SETUP_INSTRUCTION="$POLICY_CONTENT

---

MODE: ENVIRONMENT SETUP

PROJECT REQUIREMENTS:
$(cat "$REQUIREMENTS_PATH")

WORKSPACE:
- Workspace Root: $WORKSPACE_ROOT
- Project Root: $PROJECT_ROOT (create project structure here)
- Setup Artifacts: $ARTIFACTS_DIR/setup

YOUR TASK:
Set up the complete development environment based on the project requirements.

This includes:
1. Identify required programming languages, frameworks, databases, tools
2. Initialize project directory structure
3. Create configuration files (package.json, requirements.txt, etc.)
4. Set up version control (git init if needed)
5. Create initial boilerplate files
6. Document all setup steps

OUTPUT REQUIREMENTS:
Create $ARTIFACTS_DIR/setup/setup-log.md with:
- List of all tools/languages required
- Installation commands
- Project structure created
- Configuration files generated
- Verification steps
- Next steps

Begin environment setup now."

    echo "──────────────────────────────────────────────────────────────────"
    echo "🤖 Agent 3: Environment Setup"
    echo "──────────────────────────────────────────────────────────────────"
    echo "📂 Workspace: $WORKSPACE_ROOT"
    echo ""
    echo "⏳ AI is setting up development environment..."
    echo "   Configuring tools, dependencies, and project structure"
    echo ""

    # Write instruction to temp file
    TEMP_INSTRUCTION_FILE=$(mktemp)
    echo "$SETUP_INSTRUCTION" > "$TEMP_INSTRUCTION_FILE"

    echo "🔄 Starting auggie agent..." >&2

    # Debug output
    echo "DEBUG: WORKSPACE_ROOT='$WORKSPACE_ROOT'" >&2
    echo "DEBUG: TEMP_INSTRUCTION_FILE='$TEMP_INSTRUCTION_FILE'" >&2
    echo "DEBUG: Instruction file exists: $(test -f "$TEMP_INSTRUCTION_FILE" && echo 'yes' || echo 'no')" >&2

    # Try to run auggie with explicit parameter handling
    # Use explicit workspace parameter as string
    if ! auggie -p -w "$WORKSPACE_ROOT" --instruction-file "$TEMP_INSTRUCTION_FILE" 2>&1; then
        ERROR_CODE=$?
        echo "❌ Auggie command failed with exit code $ERROR_CODE" >&2
        echo "   This may be a bug in Auggie CLI (t.split is not a function error)" >&2
        echo "   Workspace: $WORKSPACE_ROOT" >&2
        echo "   Instruction file: $TEMP_INSTRUCTION_FILE" >&2
        rm -f "$TEMP_INSTRUCTION_FILE"
        exit 1
    fi

    # Cleanup
    rm -f "$TEMP_INSTRUCTION_FILE"

    echo ""
    echo "✅ Environment setup complete"
    
    if [ ! -f "$ARTIFACTS_DIR/setup/setup-log.md" ]; then
        echo "Error: setup-log.md not generated"
        exit 1
    fi
    
    echo ""
    echo "✓ Environment setup complete"
    echo "  Setup log: $ARTIFACTS_DIR/setup/setup-log.md"
    
elif [ "$MODE" == "implement" ]; then
    # ========================================================================
    # Phase 2: IMPLEMENTATION MODE
    # ========================================================================
    
    if [ -z "$TASK_ID" ]; then
        echo "Error: --task-id required for implementation mode"
        exit 1
    fi
    
    if [ ! -f "$TASK_FILE" ]; then
        echo "Error: Task file not found: $TASK_FILE"
        exit 1
    fi
    
    echo "Agent 3: Implementation Mode"
    echo "Task ID: $TASK_ID"
    echo ""
    
    # Read task details from tasks.json
    TASK_JSON=$(jq ".tasks[] | select(.id == \"$TASK_ID\")" "$TASK_FILE")
    
    if [ -z "$TASK_JSON" ]; then
        echo "Error: Task $TASK_ID not found in $TASK_FILE"
        exit 1
    fi
    
    TASK_TITLE=$(echo "$TASK_JSON" | jq -r '.title')
    TASK_DESC=$(echo "$TASK_JSON" | jq -r '.description')
    TASK_CATEGORY=$(echo "$TASK_JSON" | jq -r '.category')
    TASK_ACCEPTANCE=$(echo "$TASK_JSON" | jq -r '.acceptance_criteria | join("\n- ")')
    
    TASK_ARTIFACTS_DIR="$ARTIFACTS_DIR/tasks/$TASK_ID"
    mkdir -p "$TASK_ARTIFACTS_DIR/implementation"
    
    IMPL_INSTRUCTION="$POLICY_CONTENT

---

MODE: TASK IMPLEMENTATION

TASK DETAILS:
- ID: $TASK_ID
- Title: $TASK_TITLE
- Category: $TASK_CATEGORY
- Description: $TASK_DESC

Acceptance Criteria:
- $TASK_ACCEPTANCE

PROJECT CONTEXT:
- Project Root: $PROJECT_ROOT
- Artifacts: $TASK_ARTIFACTS_DIR
- Requirements: See below

PROJECT REQUIREMENTS:
$(cat "$REQUIREMENTS_PATH")

YOUR TASK:
Implement this specific task according to the description and acceptance criteria.
Create or modify files in $PROJECT_ROOT.

OUTPUT REQUIREMENTS:
Create $TASK_ARTIFACTS_DIR/implementation.md with:
- What was implemented
- Files created/modified
- Key decisions made
- Dependencies added
- How acceptance criteria are met

⚠️ CRITICAL: Create ONLY ONE file: implementation.md
Do NOT create summary files, notes, or additional markdown files.

Begin implementation now."

    echo "🔨 Implementing task: $TASK_TITLE"
    echo ""
    echo "⏳ AI is writing code..."
    echo ""

    # Write instruction to temp file
    TEMP_INSTRUCTION_FILE=$(mktemp)
    echo "$IMPL_INSTRUCTION" > "$TEMP_INSTRUCTION_FILE"

    # Debug output
    echo "DEBUG: WORKSPACE_ROOT='$WORKSPACE_ROOT'" >&2
    echo "DEBUG: TEMP_INSTRUCTION_FILE='$TEMP_INSTRUCTION_FILE'" >&2

    # Try to run auggie with explicit parameter handling
    if ! auggie -p -w "$WORKSPACE_ROOT" --instruction-file "$TEMP_INSTRUCTION_FILE" 2>&1; then
        ERROR_CODE=$?
        echo "❌ Auggie command failed with exit code $ERROR_CODE" >&2
        echo "   This may be a bug in Auggie CLI (t.split is not a function error)" >&2
        echo "   Workspace: $WORKSPACE_ROOT" >&2
        echo "   Instruction file: $TEMP_INSTRUCTION_FILE" >&2
        rm -f "$TEMP_INSTRUCTION_FILE"
        exit 1
    fi

    # Cleanup
    rm -f "$TEMP_INSTRUCTION_FILE"

    echo ""

    if [ ! -f "$TASK_ARTIFACTS_DIR/implementation.md" ]; then
        echo "Error: implementation.md not generated"
        exit 1
    fi

    echo ""
    echo "✓ Implementation complete for $TASK_ID"
    echo "  Summary: $TASK_ARTIFACTS_DIR/implementation.md"
    
else
    echo "Error: Invalid mode '$MODE'. Use 'setup' or 'implement'"
    exit 1
fi

exit 0
