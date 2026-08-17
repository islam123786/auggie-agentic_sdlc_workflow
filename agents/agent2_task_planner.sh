#!/bin/bash

# Agent 2: Task Planner
#
# INPUTS:
#   1. Business Requirements Document (BRD) - markdown format (.md)
#   2. Architecture Design Document - created by Agent 1 (architecture.md)
#
# OUTPUTS:
#   1. tasks.md - Human-readable task breakdown
#   2. tasks.json - Machine-readable task list with dependencies
#
# Analyzes approved architecture and BRD requirements to generate detailed task breakdown

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source environment variables if exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"
fi

# Default values
REQUIREMENTS_PATH=""
WORKSPACE_ROOT=""
POLICY_FILE="$SCRIPT_DIR/policies/task-planning.policy.md"
OUTPUT_DIR=""
PHASE="all"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --requirements-path)
            REQUIREMENTS_PATH="$2"
            shift 2
            ;;
        --workspace-root)
            WORKSPACE_ROOT="$2"
            shift 2
            ;;
        --policy-file)
            POLICY_FILE="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 --requirements-path PATH --workspace-root PATH [--policy-file PATH] [--output-dir PATH]"
            exit 1
            ;;
    esac
done

# Validation
if [ -z "$REQUIREMENTS_PATH" ]; then
    echo "Error: --requirements-path is required"
    exit 1
fi

if [ ! -f "$REQUIREMENTS_PATH" ]; then
    echo "Error: Requirements file not found: $REQUIREMENTS_PATH"
    exit 1
fi

if [ -z "$WORKSPACE_ROOT" ]; then
    echo "Error: --workspace-root is required"
    exit 1
fi

OUTPUT_DIR="${OUTPUT_DIR:-$WORKSPACE_ROOT/artifacts}"
mkdir -p "$OUTPUT_DIR"

# Load policy file
if [ ! -f "$POLICY_FILE" ]; then
    echo "Error: Policy file not found: $POLICY_FILE"
    exit 1
fi

POLICY_CONTENT=$(cat "$POLICY_FILE")

# Read architecture if exists
ARCHITECTURE_CONTENT=""
ARCHITECTURE_FILE="$WORKSPACE_ROOT/artifacts/architecture.md"
if [ -f "$ARCHITECTURE_FILE" ]; then
    ARCHITECTURE_CONTENT=$(cat "$ARCHITECTURE_FILE")
    echo "✓ Using approved architecture from: $ARCHITECTURE_FILE"
    echo ""
else
    echo "⚠️  Warning: Architecture document not found at $ARCHITECTURE_FILE"
    echo "   Task planning will proceed without architecture context"
    echo ""
fi

# Build task planning instruction
TASK_INSTRUCTION="SCOPE: Analyze ALL requirements and create tasks for implementing the complete application."

# Build instruction for auggie
ARCHITECTURE_SECTION=""
if [ -n "$ARCHITECTURE_CONTENT" ]; then
    ARCHITECTURE_SECTION="
APPROVED ARCHITECTURE:

$ARCHITECTURE_CONTENT

---

CRITICAL: Use the technology stack and architecture decisions from above.
Do NOT propose different technologies or architectures."
fi

TASK_PLANNING_INSTRUCTION="$POLICY_CONTENT

---

EXECUTION CONTEXT:

PROJECT REQUIREMENTS:
$(cat "$REQUIREMENTS_PATH")

$ARCHITECTURE_SECTION

WORKSPACE:
- Workspace Root: $WORKSPACE_ROOT
- Output Directory: $OUTPUT_DIR

$TASK_INSTRUCTION

IMPORTANT: Create the following files in $OUTPUT_DIR:

1. tasks.md - Human-readable task breakdown with:
   - Executive summary
   - Task categories (Setup, Infrastructure, Implementation, Testing, Documentation)
   - Detailed task list with sequence numbers
   - Dependencies clearly marked
   - Execution timeline/phases

2. tasks.json - Machine-readable task list in this exact format:
{
  \"project_name\": \"Project Name\",
  \"total_tasks\": 15,
  \"estimated_duration\": \"40 hours\",
  \"tasks\": [
    {
      \"id\": \"task-001\",
      \"title\": \"Task title\",
      \"description\": \"Detailed description of what needs to be done\",
      \"sequence\": 1,
      \"dependencies\": [],
      \"category\": \"setup\",
      \"estimated_effort\": \"2h\",
      \"acceptance_criteria\": [
        \"Criterion 1\",
        \"Criterion 2\"
      ]
    }
  ]
}

Categories must be one of: setup, infrastructure, implementation, integration, testing, documentation

Begin analysis and task planning now."

# Run Auggie agent
echo "──────────────────────────────────────────────────────────────────"
echo "🤖 Agent 2: Task Planner"
echo "──────────────────────────────────────────────────────────────────"
echo ""
echo "📥 INPUTS:"
echo "   1. 📄 Business Requirements (BRD): $REQUIREMENTS_PATH"
if [ -n "$ARCHITECTURE_CONTENT" ]; then
    echo "   2. 🏗️  Architecture Design: $ARCHITECTURE_FILE ✓"
else
    echo "   2. 🏗️  Architecture Design: (not found - will proceed without)"
fi
echo ""
echo "📤 OUTPUTS:"
echo "   📄 Task Breakdown: $OUTPUT_DIR/tasks.md"
echo "   📄 Task List (JSON): $OUTPUT_DIR/tasks.json"
echo ""
echo "⏳ AI is analyzing BRD + Architecture and creating task breakdown..."
echo "   This typically takes 5-10 minutes"
echo "   Please wait - no output is normal during AI processing"
echo ""

# Write instruction to temp file
TEMP_INSTRUCTION_FILE=$(mktemp)
echo "$TASK_PLANNING_INSTRUCTION" > "$TEMP_INSTRUCTION_FILE"

echo "🔄 Starting auggie agent..." >&2

auggie -p -w "$WORKSPACE_ROOT" --instruction-file "$TEMP_INSTRUCTION_FILE"

# Cleanup
rm -f "$TEMP_INSTRUCTION_FILE"

echo ""
echo "✅ Task planning AI processing complete"

# Validate outputs
if [ ! -f "$OUTPUT_DIR/tasks.md" ]; then
    echo "Error: tasks.md not generated"
    exit 1
fi

if [ ! -f "$OUTPUT_DIR/tasks.json" ]; then
    echo "Error: tasks.json not generated"
    exit 1
fi

# Validate JSON format
if ! jq empty "$OUTPUT_DIR/tasks.json" 2>/dev/null; then
    echo "Error: tasks.json is not valid JSON"
    exit 1
fi

echo ""
echo "✓ Task planning complete"
echo "  - Tasks markdown: $OUTPUT_DIR/tasks.md"
echo "  - Tasks JSON: $OUTPUT_DIR/tasks.json"
echo ""

# Display summary
TASK_COUNT=$(jq -r '.total_tasks' "$OUTPUT_DIR/tasks.json")
echo "Summary: $TASK_COUNT tasks generated"

exit 0
