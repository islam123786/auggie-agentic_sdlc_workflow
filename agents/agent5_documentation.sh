#!/bin/bash

# Agent 5: Documentation
# Generate comprehensive design documentation for completed tasks

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
POLICY_FILE="$SCRIPT_DIR/policies/documentation.policy.md"

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
if [ -z "$WORKSPACE_ROOT" ] || [ -z "$TASK_ID" ] || [ -z "$TASK_FILE" ]; then
    echo "Error: --workspace-root, --task-id, and --task-file are required"
    exit 1
fi

if [ ! -f "$TASK_FILE" ]; then
    echo "Error: Task file not found: $TASK_FILE"
    exit 1
fi

if [ ! -f "$POLICY_FILE" ]; then
    echo "Error: Policy file not found: $POLICY_FILE"
    exit 1
fi

echo "Agent 5: Documentation"
echo "Task ID: $TASK_ID"
echo ""

# Read task details
TASK_JSON=$(jq ".tasks[] | select(.id == \"$TASK_ID\")" "$TASK_FILE")
TASK_TITLE=$(echo "$TASK_JSON" | jq -r '.title')
TASK_DESC=$(echo "$TASK_JSON" | jq -r '.description')
TASK_CATEGORY=$(echo "$TASK_JSON" | jq -r '.category')

TASK_ARTIFACTS_DIR="$WORKSPACE_ROOT/artifacts/tasks/$TASK_ID"
PROJECT_ROOT="$WORKSPACE_ROOT/project-code"

POLICY_CONTENT=$(cat "$POLICY_FILE")

# Gather context from previous steps
IMPLEMENTATION_SUMMARY=""
if [ -f "$TASK_ARTIFACTS_DIR/implementation.md" ]; then
    IMPLEMENTATION_SUMMARY=$(cat "$TASK_ARTIFACTS_DIR/implementation.md")
fi

TEST_RESULTS=""
if [ -f "$TASK_ARTIFACTS_DIR/testing.md" ]; then
    TEST_RESULTS=$(cat "$TASK_ARTIFACTS_DIR/testing.md")
fi

# Generate documentation
DOC_INSTRUCTION="$POLICY_CONTENT

---

TASK TO DOCUMENT:
- ID: $TASK_ID
- Title: $TASK_TITLE
- Category: $TASK_CATEGORY
- Description: $TASK_DESC

IMPLEMENTATION SUMMARY:
$IMPLEMENTATION_SUMMARY

TEST RESULTS:
$TEST_RESULTS

PROJECT ROOT: $PROJECT_ROOT

YOUR TASK:
Create comprehensive design documentation for this completed task.

OUTPUT REQUIREMENTS:
Create $TASK_ARTIFACTS_DIR/documentation.md with:

1. **Overview**: What was implemented and why
2. **Architecture**: High-level design decisions
3. **Implementation Details**: How it works
4. **API Documentation**: Endpoints, parameters, responses (if applicable)
5. **Data Models**: Database schemas, data structures (if applicable)
6. **Architecture Diagrams**: Using Mermaid syntax (if helpful)
7. **Code Examples**: Usage examples
8. **Dependencies**: External libraries or services used
9. **Configuration**: Environment variables, settings
10. **Testing**: How to test this feature
11. **Known Limitations**: Any limitations or caveats
12. **Future Considerations**: Potential improvements

Make it comprehensive but concise. Use Mermaid diagrams where helpful.

⚠️ CRITICAL: Create ONLY ONE file: documentation.md
Do NOT create summary files, diagram files, or additional markdown files.

Begin documentation generation now."

echo "──────────────────────────────────────────────────────────────────"
echo "🤖 Agent 5: Documentation"
echo "──────────────────────────────────────────────────────────────────"
echo "📋 Task: $TASK_TITLE"
echo ""
echo "📝 AI is generating design documentation..."
echo "   Creating architecture diagrams and technical details"
echo ""

# Write instruction to temp file
TEMP_INSTRUCTION_FILE=$(mktemp)
echo "$DOC_INSTRUCTION" > "$TEMP_INSTRUCTION_FILE"

auggie -p -w "$WORKSPACE_ROOT" --instruction-file "$TEMP_INSTRUCTION_FILE"

# Cleanup
rm -f "$TEMP_INSTRUCTION_FILE"

echo ""
echo "✅ Documentation generated"

if [ ! -f "$TASK_ARTIFACTS_DIR/documentation.md" ]; then
    echo "Error: documentation.md not generated"
    exit 1
fi

echo ""
echo "✓ Documentation complete for $TASK_ID"
echo "  Design doc: $TASK_ARTIFACTS_DIR/documentation.md"

exit 0
