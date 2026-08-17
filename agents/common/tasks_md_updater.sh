#!/bin/bash

# Helper script to update tasks.md and tasks.json with task completion status
# Updates checkboxes from [ ] to [x] for completed tasks
# Adds completion status and timestamp to tasks.json

set -e

# Function to mark a task as complete in tasks.json
update_tasks_json() {
    local tasks_json_file="$1"
    local task_id="$2"
    local timestamp="$3"

    if [ ! -f "$tasks_json_file" ]; then
        echo "Warning: tasks.json not found at $tasks_json_file"
        return 1
    fi

    # Create atomic temp file
    local temp_file="${tasks_json_file}.tmp.$$"

    # Use jq to add status and completed_at fields to the task
    jq --arg task_id "$task_id" --arg timestamp "$timestamp" '
        .tasks = [
            .tasks[] |
            if .id == $task_id then
                . + {
                    "status": "completed",
                    "completed_at": $timestamp
                }
            else
                .
            end
        ]
    ' "$tasks_json_file" > "$temp_file"

    # Atomic move
    if [ -s "$temp_file" ]; then
        mv "$temp_file" "$tasks_json_file"
        echo "✓ Updated tasks.json: marked $task_id as completed at $timestamp"
        return 0
    else
        rm -f "$temp_file"
        echo "Warning: Failed to update tasks.json (empty output)"
        return 1
    fi
}

# Function to mark a task as complete in tasks.md
mark_task_complete() {
    local tasks_md_file="$1"
    local task_id="$2"
    local timestamp="$3"
    
    if [ ! -f "$tasks_md_file" ]; then
        echo "Warning: tasks.md not found at $tasks_md_file"
        return 1
    fi

    # Extract task number from task_id (e.g., task-001 -> 001)
    task_num=$(echo "$task_id" | sed 's/task-//')

    # Use atomic file operations - write to temp file first
    local temp_file="${tasks_md_file}.tmp.$$"

    # First, find the line number of the task header
    task_header_line=$(grep -n "^### Task ${task_num}:" "$tasks_md_file" | cut -d: -f1)

    if [ -z "$task_header_line" ]; then
        echo "Warning: Task $task_num not found in tasks.md"
        return 1
    fi

    # Find the next task header or end of file
    next_task_line=$(tail -n +$((task_header_line + 1)) "$tasks_md_file" | grep -n "^### Task [0-9]" | head -1 | cut -d: -f1)

    if [ -z "$next_task_line" ]; then
        # No next task, process until end of file
        end_line=$(wc -l < "$tasks_md_file")
    else
        # Process until next task
        end_line=$((task_header_line + next_task_line - 1))
    fi

    # Update checkboxes in the task section and add completion timestamp
    # Write to temp file atomically
    awk -v task_start="$task_header_line" \
        -v task_end="$end_line" \
        -v timestamp="$timestamp" \
        -v task_id="$task_id" '
    NR == task_start + 1 && !/^\*\*Completed:/ {
        print "**Completed:** ✅ " timestamp
    }
    {
        if (NR >= task_start && NR <= task_end && /^- \[ \]/) {
            gsub(/^- \[ \]/, "- [x]")
        }
        print
    }
    ' "$tasks_md_file" > "$temp_file"

    # Atomic move if temp file is valid
    if [ -s "$temp_file" ]; then
        mv "$temp_file" "$tasks_md_file"
        echo "✓ Updated tasks.md: marked $task_id as complete"
        return 0
    else
        rm -f "$temp_file"
        echo "Warning: Failed to update tasks.md (empty output)"
        return 1
    fi
}

# Main execution if called directly
if [ "${BASH_SOURCE[0]}" == "$0" ]; then
    if [ $# -lt 2 ] || [ $# -gt 3 ]; then
        echo "Usage: $0 <tasks_md_file> <task_id> [timestamp]"
        echo "Example: $0 /path/to/tasks.md task-001"
        echo "Example: $0 /path/to/tasks.md task-001 '2026-06-11T10:30:00'"
        exit 1
    fi

    TASKS_MD_FILE="$1"
    TASK_ID="$2"
    TIMESTAMP="${3:-$(date -u +"%Y-%m-%dT%H:%M:%S")}"

    # Derive tasks.json path from tasks.md path
    TASKS_DIR=$(dirname "$TASKS_MD_FILE")
    TASKS_JSON_FILE="${TASKS_DIR}/tasks.json"

    # Update both files
    SUCCESS=true

    # Update tasks.json first
    if [ -f "$TASKS_JSON_FILE" ]; then
        if ! update_tasks_json "$TASKS_JSON_FILE" "$TASK_ID" "$TIMESTAMP"; then
            SUCCESS=false
        fi
    else
        echo "Warning: tasks.json not found at $TASKS_JSON_FILE (skipping)"
    fi

    # Update tasks.md
    if ! mark_task_complete "$TASKS_MD_FILE" "$TASK_ID" "$TIMESTAMP"; then
        SUCCESS=false
    fi

    if [ "$SUCCESS" = true ]; then
        exit 0
    else
        exit 1
    fi
fi
