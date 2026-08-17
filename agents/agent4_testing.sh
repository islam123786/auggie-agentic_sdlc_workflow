#!/bin/bash

# Agent 4: Testing
# Generate test plan and execute tests for a completed task

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source environment variables if exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"
fi

# Source git helper functions
if [ -f "$SCRIPT_DIR/common/git_helper.sh" ]; then
    source "$SCRIPT_DIR/common/git_helper.sh"
fi

# Default values
WORKSPACE_ROOT=""
TASK_ID=""
TASK_FILE=""
POLICY_FILE="$SCRIPT_DIR/policies/testing.policy.md"
MAX_RETRIES=2
TEST_TIMEOUT=600  # 10 minutes
FIX_TIMEOUT=300   # 5 minutes
SMART_RETRY="true"

# GitHub Integration
GITHUB_ENABLED="false"
GITHUB_AUTO_COMMIT="false"
GITHUB_REPO_URL=""
GITHUB_BRANCH="main"
GITHUB_COMMIT_PREFIX="[AI-Generated]"
GITHUB_USER_NAME=""
GITHUB_USER_EMAIL=""

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
        --max-retries)
            MAX_RETRIES="$2"
            shift 2
            ;;
        --test-timeout)
            TEST_TIMEOUT="$2"
            shift 2
            ;;
        --fix-timeout)
            FIX_TIMEOUT="$2"
            shift 2
            ;;
        --smart-retry)
            SMART_RETRY="$2"
            shift 2
            ;;
        --policy-file)
            POLICY_FILE="$2"
            shift 2
            ;;
        --github-enabled)
            GITHUB_ENABLED="$2"
            shift 2
            ;;
        --github-auto-commit)
            GITHUB_AUTO_COMMIT="$2"
            shift 2
            ;;
        --github-repo-url)
            GITHUB_REPO_URL="$2"
            shift 2
            ;;
        --github-branch)
            GITHUB_BRANCH="$2"
            shift 2
            ;;
        --github-commit-prefix)
            GITHUB_COMMIT_PREFIX="$2"
            shift 2
            ;;
        --github-user-name)
            GITHUB_USER_NAME="$2"
            shift 2
            ;;
        --github-user-email)
            GITHUB_USER_EMAIL="$2"
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

# ============================================================================
# Helper Functions
# ============================================================================

# Function to run command with timeout
run_with_timeout() {
    local timeout_duration=$1
    local temp_file=$2
    local log_prefix=$3

    echo "⏱️  Timeout set to ${timeout_duration}s"

    # Detect which timeout command to use
    local TIMEOUT_CMD=""
    if command -v gtimeout &> /dev/null; then
        TIMEOUT_CMD="gtimeout"  # macOS with GNU coreutils (brew install coreutils)
    elif command -v timeout &> /dev/null; then
        TIMEOUT_CMD="timeout"   # Linux
    else
        echo "⚠️  Warning: timeout command not available, running without timeout"
        # Run without timeout
        if auggie -p -w "$WORKSPACE_ROOT" --instruction-file "$temp_file"; then
            return 0
        else
            return $?
        fi
    fi

    # Run auggie with timeout
    if $TIMEOUT_CMD "${timeout_duration}s" auggie -p -w "$WORKSPACE_ROOT" --instruction-file "$temp_file"; then
        return 0
    else
        local exit_code=$?
        if [ $exit_code -eq 124 ]; then
            echo ""
            echo "⚠️  WARNING: ${log_prefix} timed out after ${timeout_duration}s"
            echo "This may indicate a hanging process or very slow execution."
            return 124
        else
            return $exit_code
        fi
    fi
}

# Function to extract error signature from test results
extract_error_signature() {
    local results_file=$1

    # Extract key error indicators (first 3 error messages)
    grep -A 3 "Error:\|FAILED:\|AssertionError:\|Exception:" "$results_file" 2>/dev/null | head -20 | md5sum | cut -d' ' -f1
}

# Function to check if errors are identical
are_errors_identical() {
    local prev_sig=$1
    local curr_sig=$2

    if [ -z "$prev_sig" ] || [ -z "$curr_sig" ]; then
        return 1  # Not identical if either is empty
    fi

    [ "$prev_sig" == "$curr_sig" ]
}

echo "Agent 4: Testing"
echo "Task ID: $TASK_ID"
echo "Configuration:"
echo "  Max Retries: $MAX_RETRIES"
echo "  Test Timeout: ${TEST_TIMEOUT}s"
echo "  Fix Timeout: ${FIX_TIMEOUT}s"
echo "  Smart Retry: $SMART_RETRY"
echo ""

# Read task details
TASK_JSON=$(jq ".tasks[] | select(.id == \"$TASK_ID\")" "$TASK_FILE")
TASK_TITLE=$(echo "$TASK_JSON" | jq -r '.title')
TASK_DESC=$(echo "$TASK_JSON" | jq -r '.description')
TASK_CATEGORY=$(echo "$TASK_JSON" | jq -r '.category')

TASK_ARTIFACTS_DIR="$WORKSPACE_ROOT/artifacts/tasks/$TASK_ID"
PROJECT_ROOT="$WORKSPACE_ROOT/project-code"

POLICY_CONTENT=$(cat "$POLICY_FILE")

# ============================================================================
# Step 1: Generate Test Plan
# ============================================================================

echo "Step 1: Generating test plan..."
echo ""

TEST_PLAN_INSTRUCTION="$POLICY_CONTENT

---

MODE: TEST PLAN GENERATION

TASK UNDER TEST:
- ID: $TASK_ID
- Title: $TASK_TITLE
- Category: $TASK_CATEGORY
- Description: $TASK_DESC

IMPLEMENTATION:
$(cat "$TASK_ARTIFACTS_DIR/implementation.md" 2>/dev/null || echo "No implementation summary available")

PROJECT ROOT: $PROJECT_ROOT

YOUR TASK:
Create a comprehensive test plan for this task.

OUTPUT REQUIREMENTS:
Create $TASK_ARTIFACTS_DIR/testing.md with the following sections:

# Testing Report: $TASK_TITLE

## Test Plan
1. Test strategy (what approach to use)
2. Test scenarios (list of scenarios to test)
3. Test cases (specific test cases with inputs and expected outputs)
4. Test data requirements
5. Testing tools/frameworks to use

⚠️ CRITICAL: Create ONLY ONE file: testing.md
This file will be appended to with test results and fix summaries.

Begin test plan generation now."

echo "──────────────────────────────────────────────────────────────────"
echo "🤖 Agent 3: Test Planning"
echo "──────────────────────────────────────────────────────────────────"
echo "📋 Task: $TASK_TITLE"
echo ""
echo "⏳ AI is creating test plan..."
echo ""

# Write instruction to temp file
TEMP_INSTRUCTION_FILE=$(mktemp)
echo "$TEST_PLAN_INSTRUCTION" > "$TEMP_INSTRUCTION_FILE"

auggie -p -w "$WORKSPACE_ROOT" --instruction-file "$TEMP_INSTRUCTION_FILE"

# Cleanup
rm -f "$TEMP_INSTRUCTION_FILE"

echo ""
echo "✅ Test plan created"

if [ ! -f "$TASK_ARTIFACTS_DIR/testing.md" ]; then
    echo "Error: testing.md not generated"
    exit 1
fi

echo "✓ Test plan generated in testing.md"
echo ""

# ============================================================================
# Pre-Test Validation: Check for Common Test Fixture Issues
# ============================================================================

detect_database_fixture_issues() {
    local conftest_file="$1"
    local warnings=()

    if [ -f "$conftest_file" ]; then
        local content=$(cat "$conftest_file")

        # Check for session-scoped fixture with :memory: database
        if echo "$content" | grep -q "scope='session'" && echo "$content" | grep -q ":memory:"; then
            warnings+=("⚠️  Session-scoped fixture with :memory: database detected")
            warnings+=("   This commonly causes 'index already exists' or 'table already exists' errors")
            warnings+=("   Recommendation: Change to scope='function' for proper test isolation")
        fi

        # Check for missing checkfirst=True
        if echo "$content" | grep -q "create_all" && ! echo "$content" | grep -q "checkfirst=True"; then
            warnings+=("⚠️  create_all() without checkfirst=True detected")
            warnings+=("   This can cause 'already exists' errors on schema recreation")
            warnings+=("   Recommendation: Add checkfirst=True parameter")
        fi

        # Check for missing cleanup (drop_all)
        if echo "$content" | grep -q "create_all" && ! echo "$content" | grep -q "drop_all"; then
            warnings+=("⚠️  Missing drop_all() cleanup in fixture teardown")
            warnings+=("   This can cause schema persistence across tests")
            warnings+=("   Recommendation: Add 'await conn.run_sync(Base.metadata.drop_all)' cleanup")
        fi

        # Check for async fixture without proper dispose
        if echo "$content" | grep -q "create_async_engine" && ! echo "$content" | grep -q "dispose()"; then
            warnings+=("⚠️  Async engine without proper dispose() cleanup")
            warnings+=("   This can cause connection leaks and test hangs")
            warnings+=("   Recommendation: Add 'await test_engine.dispose()' in cleanup")
        fi
    fi

    # Print warnings if any
    if [ ${#warnings[@]} -gt 0 ]; then
        echo ""
        echo "╔════════════════════════════════════════════════════════════════════╗"
        echo "║  🔍 Pre-Test Validation: Potential Test Fixture Issues Detected   ║"
        echo "╚════════════════════════════════════════════════════════════════════╝"
        echo ""
        for warning in "${warnings[@]}"; do
            echo "$warning"
        done
        echo ""
        echo "These issues may cause test failures. The testing agent will attempt"
        echo "to auto-fix them if tests fail with database-related errors."
        echo ""
        return 1
    fi

    return 0
}

# Check for conftest.py in common test directories
CONFTEST_PATHS=(
    "$PROJECT_ROOT/tests/conftest.py"
    "$PROJECT_ROOT/backend/tests/conftest.py"
    "$PROJECT_ROOT/src/tests/conftest.py"
    "$PROJECT_ROOT/test/conftest.py"
)

echo "🔍 Pre-Test Validation: Checking test fixtures..."
echo ""

FIXTURE_ISSUES_DETECTED=false
for conftest_path in "${CONFTEST_PATHS[@]}"; do
    if [ -f "$conftest_path" ]; then
        echo "   Checking: $conftest_path"
        if ! detect_database_fixture_issues "$conftest_path"; then
            FIXTURE_ISSUES_DETECTED=true
        fi
    fi
done

if [ "$FIXTURE_ISSUES_DETECTED" == "false" ]; then
    echo "   ✓ No obvious fixture issues detected"
    echo ""
fi

# ============================================================================
# Step 2: Execute Tests with Retry
# ============================================================================

echo "Step 2: Executing tests..."
echo ""

RETRY_COUNT=0
TEST_PASSED=false
PREVIOUS_ERROR_SIG=""

while [ $RETRY_COUNT -le $MAX_RETRIES ] && [ "$TEST_PASSED" == "false" ]; do
    ATTEMPT=$((RETRY_COUNT + 1))

    echo "──────────────────────────────────────────────────────────────────"
    echo "🧪 Test Attempt $ATTEMPT of $((MAX_RETRIES + 1))"
    echo "──────────────────────────────────────────────────────────────────"
    
    TEST_EXEC_INSTRUCTION="$POLICY_CONTENT

---

MODE: TEST EXECUTION

TASK: $TASK_ID - $TASK_TITLE

Test Plan: Read from $TASK_ARTIFACTS_DIR/testing.md (Test Plan section)

PROJECT ROOT: $PROJECT_ROOT

⚠️ CRITICAL TEST ENVIRONMENT SETUP:
The conftest.py file has already been modified to set EMBEDDING_MODEL=openai at the top.
This prevents SSL certificate errors when the EmbeddingService module loads during import.

VERIFY the fix is in place:
- tests/conftest.py should have these lines at the TOP (after docstring):
  import os
  os.environ['EMBEDDING_MODEL'] = 'openai'

If the fix is NOT present, add those 2 lines at the very top of conftest.py BEFORE any app imports.

Test execution steps:
1. Navigate to project root: cd $PROJECT_ROOT
2. Activate virtual environment: source .venv/bin/activate
3. Run tests: pytest tests/ -v --cov=app

YOUR TASK:
1. Verify conftest.py has the EMBEDDING_MODEL fix (check lines 7-10)
2. Navigate to project root
3. Activate virtual environment
4. Execute the tests defined in the test plan
5. Run pytest with appropriate flags
6. Report results clearly

OUTPUT REQUIREMENTS:
APPEND to $TASK_ARTIFACTS_DIR/testing.md (use str-replace-editor tool) with a new section:

---

## Test Execution - Attempt $ATTEMPT

**Date:** [timestamp]
**Summary:** PASSED | FAILED

### Test Results
- Total tests: N
- Passed: N
- Failed: N
- Skipped: N

### Test Execution Log
[Detailed test output]

### Failed Tests (if any)
[Error messages and stack traces]

### Coverage
[Coverage information if available]

⚠️ CRITICAL: APPEND to existing testing.md file, do NOT create a new file.
Use str-replace-editor to add content at the end of the file.

Begin test execution now."

    # Write instruction to temp file
    TEMP_INSTRUCTION_FILE=$(mktemp)
    echo "$TEST_EXEC_INSTRUCTION" > "$TEMP_INSTRUCTION_FILE"

    # Run tests with timeout
    if ! run_with_timeout "$TEST_TIMEOUT" "$TEMP_INSTRUCTION_FILE" "Test execution"; then
        TEST_EXIT_CODE=$?
        rm -f "$TEMP_INSTRUCTION_FILE"

        if [ $TEST_EXIT_CODE -eq 124 ]; then
            echo "❌ Test execution timed out. Skipping retries."
            exit 1
        fi
    fi

    # Cleanup
    rm -f "$TEMP_INSTRUCTION_FILE"

    echo ""

    if [ ! -f "$TASK_ARTIFACTS_DIR/testing.md" ]; then
        echo "⚠️  Warning: testing.md not updated with test results"
        echo "Attempting to continue..."
    fi

    # Check if tests passed (look for PASSED in summary in the testing.md file)
    # Match both "Summary: PASSED" and "**Summary**: ✅ **PASSED**" formats
    if grep -qE "Attempt $ATTEMPT.*PASSED" "$TASK_ARTIFACTS_DIR/testing.md" 2>/dev/null || \
       grep -qE "Summary.*PASSED" "$TASK_ARTIFACTS_DIR/testing.md" 2>/dev/null; then
        TEST_PASSED=true
        echo ""
        echo "✅ Tests PASSED on attempt $ATTEMPT"
        echo ""
    else
        echo ""
        echo "❌ Tests FAILED on attempt $ATTEMPT"
        echo ""

        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            # Smart retry: Check if error is identical to previous attempt
            if [ "$SMART_RETRY" == "true" ] && [ $RETRY_COUNT -gt 0 ]; then
                CURRENT_ERROR_SIG=$(extract_error_signature "$TASK_ARTIFACTS_DIR/testing.md")

                if are_errors_identical "$PREVIOUS_ERROR_SIG" "$CURRENT_ERROR_SIG"; then
                    echo "🔍 Smart Retry: Detected identical error pattern"
                    echo "   Error signature: ${CURRENT_ERROR_SIG:0:12}..."
                    echo "   Previous fix did not resolve the issue."
                    echo "   Skipping additional retries to save time."
                    echo ""
                    echo "❌ ERROR: Tests FAILED with repeating errors after $ATTEMPT attempts"
                    echo "See: $TASK_ARTIFACTS_DIR/testing.md"
                    exit 1
                fi

                PREVIOUS_ERROR_SIG=$CURRENT_ERROR_SIG
            else
                # Store first error signature
                PREVIOUS_ERROR_SIG=$(extract_error_signature "$TASK_ARTIFACTS_DIR/testing.md")
            fi

            echo "🔧 Attempting auto-fix..."
            echo ""

            # Detect specific error patterns for targeted fixes
            ERROR_CONTEXT=""
            if grep -q "already exists" "$TASK_ARTIFACTS_DIR/testing.md" 2>/dev/null; then
                if grep -qE "(index|table).*already exists" "$TASK_ARTIFACTS_DIR/testing.md"; then
                    echo "   🔍 Detected: Database schema conflict error (index/table already exists)"
                    ERROR_CONTEXT="

⚠️ CRITICAL ERROR PATTERN DETECTED: Database Schema Conflict

The test output shows 'index already exists' or 'table already exists' errors.
This is a KNOWN PATTERN with SQLAlchemy async tests using in-memory SQLite.

ROOT CAUSE: Session-scoped pytest fixture with improper cleanup

REQUIRED FIX (Apply to conftest.py):
1. Change fixture scope from 'session' to 'function'
2. Add checkfirst=True to Base.metadata.create_all()
3. Add cleanup: await conn.run_sync(Base.metadata.drop_all)
4. Add disposal: await test_engine.dispose()

See the 'Database Testing Best Practices' section in the testing policy for the exact pattern.

This is NOT an implementation bug - it's a test fixture configuration issue.
Fix the conftest.py file, NOT the application code."
                fi
            fi

            if grep -q "timed out\|timeout" "$TASK_ARTIFACTS_DIR/testing.md" 2>/dev/null; then
                echo "   🔍 Detected: Test timeout error"
                ERROR_CONTEXT="$ERROR_CONTEXT

⚠️ TIMEOUT DETECTED: Tests are hanging or taking too long

Possible causes:
1. Database connections not properly closed (check async context managers)
2. Infinite loops in test code
3. Missing await on async operations
4. Session-scoped fixtures causing connection issues

Check for proper cleanup in conftest.py fixtures."
            fi

            # Auto-fix instruction
            FIX_INSTRUCTION="$POLICY_CONTENT

---

MODE: TEST FIX

TASK: $TASK_ID - $TASK_TITLE

Test Results: Read from $TASK_ARTIFACTS_DIR/testing.md (Attempt $ATTEMPT section)

PROJECT ROOT: $PROJECT_ROOT
$ERROR_CONTEXT

YOUR TASK:
Analyze the test failures and fix the issues.

IMPORTANT:
- For database 'already exists' errors: Fix the TEST FIXTURE (conftest.py), NOT the implementation
- For other errors: Fix the implementation code
- Do NOT modify the test plan
- Be thorough but efficient - you have limited time
- Refer to 'Common Test Failure Patterns & Auto-Fixes' in the policy above

OUTPUT REQUIREMENTS:
APPEND to $TASK_ARTIFACTS_DIR/testing.md (use str-replace-editor tool) with a new section:

---

## Fix Summary - Attempt $ATTEMPT

**Date:** [timestamp]

### Issues Identified
1. [Issue description]
2. [Issue description]

### Fixes Applied
1. [Fix description]
2. [Fix description]

### Files Modified
- [file path]: [what was changed]
- [file path]: [what was changed]

⚠️ CRITICAL: APPEND to existing testing.md file, do NOT create a new file.
Use str-replace-editor to add content at the end of the file.

Begin test fix now."

            # Write instruction to temp file
            TEMP_INSTRUCTION_FILE=$(mktemp)
            echo "$FIX_INSTRUCTION" > "$TEMP_INSTRUCTION_FILE"

            # Run fix with timeout
            if ! run_with_timeout "$FIX_TIMEOUT" "$TEMP_INSTRUCTION_FILE" "Fix execution"; then
                FIX_EXIT_CODE=$?
                rm -f "$TEMP_INSTRUCTION_FILE"

                if [ $FIX_EXIT_CODE -eq 124 ]; then
                    echo "❌ Fix execution timed out. Skipping additional retries."
                    exit 1
                fi
            fi

            # Cleanup
            rm -f "$TEMP_INSTRUCTION_FILE"

            echo ""
            echo "✅ Auto-fix attempt completed"
            echo "📝 Fix summary appended to: testing.md"

            echo "🔄 Retrying tests..."
            echo ""
            RETRY_COUNT=$((RETRY_COUNT + 1))
        else
            echo ""
            echo "❌ ERROR: Tests FAILED after $((MAX_RETRIES + 1)) attempts"
            echo "See: $TASK_ARTIFACTS_DIR/testing.md"
            exit 1
        fi
    fi
done

echo ""
echo "✓ Testing complete for $TASK_ID"
echo "  All testing info: $TASK_ARTIFACTS_DIR/testing.md"

# ============================================================================
# GitHub Integration: Removed - Handled by Workflow Engine
# ============================================================================
# NOTE: Git commits are now handled by the workflow engine after ALL agents
# complete (Implementation → Testing → Documentation). This ensures a single
# commit per task with all changes included.
# See: orchestrator/workflow_engine.py _git_commit_task() (line 537-589)

exit 0
