#!/bin/bash

# Common functions for all agents
# Source this file in agent scripts: source "$(dirname "${BASH_SOURCE[0]}")/common/functions.sh"

# ============================================================================
# Argument Parsing Utilities
# ============================================================================

# Parse common arguments used across agents
# Usage: parse_common_args "$@"
# Sets: WORKSPACE_ROOT, POLICY_FILE
parse_common_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --workspace-root)
                WORKSPACE_ROOT="$2"
                shift 2
                ;;
            --policy-file)
                POLICY_FILE="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
}

# ============================================================================
# Validation Functions
# ============================================================================

# Validate that required environment variables are set
validate_required_vars() {
    local missing=()
    
    for var in "$@"; do
        if [ -z "${!var}" ]; then
            missing+=("$var")
        fi
    done
    
    if [ ${#missing[@]} -gt 0 ]; then
        echo "Error: Missing required variables: ${missing[*]}"
        return 1
    fi
    
    return 0
}

# Validate file exists
validate_file_exists() {
    local file_path=$1
    local description=$2
    
    if [ ! -f "$file_path" ]; then
        echo "Error: $description not found: $file_path"
        return 1
    fi
    
    return 0
}

# Validate directory exists or create it
ensure_directory() {
    local dir_path=$1
    
    if [ ! -d "$dir_path" ]; then
        mkdir -p "$dir_path" || {
            echo "Error: Failed to create directory: $dir_path"
            return 1
        }
    fi
    
    return 0
}

# ============================================================================
# Temp File Management
# ============================================================================

# Global array to track temp files for cleanup
declare -a TEMP_FILES=()

# Create a temp file and register it for cleanup
create_temp_file() {
    local temp_file
    temp_file=$(mktemp) || {
        echo "Error: Failed to create temporary file"
        return 1
    }
    
    TEMP_FILES+=("$temp_file")
    echo "$temp_file"
}

# Cleanup all registered temp files
cleanup_temp_files() {
    for file in "${TEMP_FILES[@]}"; do
        if [ -f "$file" ]; then
            rm -f "$file"
        fi
    done
    TEMP_FILES=()
}

# Setup trap for cleanup on exit
setup_cleanup_trap() {
    trap cleanup_temp_files EXIT INT TERM
}

# ============================================================================
# Auggie Execution Helpers
# ============================================================================

# Run auggie with timeout support
# Usage: run_auggie_with_timeout <timeout_seconds> <instruction_text> <workspace_root> [<log_prefix>]
run_auggie_with_timeout() {
    local timeout_duration=$1
    local instruction_text=$2
    local workspace=$3
    local log_prefix=${4:-"AI agent"}
    
    local temp_file
    temp_file=$(create_temp_file) || return 1
    
    echo "$instruction_text" > "$temp_file"
    
    echo "⏱️  Timeout set to ${timeout_duration}s"
    echo "⏳ Running $log_prefix..."
    echo ""
    
    # Run auggie with timeout
    if timeout "${timeout_duration}s" auggie -p -w "$workspace" --instruction-file "$temp_file"; then
        return 0
    else
        local exit_code=$?
        if [ $exit_code -eq 124 ]; then
            echo ""
            echo "⚠️  WARNING: $log_prefix timed out after ${timeout_duration}s"
            echo "This may indicate a hanging process or very slow execution."
            return 124
        else
            return $exit_code
        fi
    fi
}

# Run auggie without timeout
run_auggie() {
    local instruction_text=$1
    local workspace=$2
    
    local temp_file
    temp_file=$(create_temp_file) || return 1
    
    echo "$instruction_text" > "$temp_file"
    auggie -p -w "$workspace" --instruction-file "$temp_file"
}

# ============================================================================
# Output Formatting
# ============================================================================

# Print section header
print_header() {
    local title=$1
    echo "════════════════════════════════════════════════════════════════════"
    echo "$title"
    echo "════════════════════════════════════════════════════════════════════"
}

# Print subsection header
print_subheader() {
    local title=$1
    echo "──────────────────────────────────────────────────────────────────"
    echo "$title"
    echo "──────────────────────────────────────────────────────────────────"
}

# Print success message
print_success() {
    echo "✅ $1"
}

# Print error message
print_error() {
    echo "❌ ERROR: $1" >&2
}

# Print warning message
print_warning() {
    echo "⚠️  WARNING: $1"
}

# Print info message
print_info() {
    echo "ℹ️  $1"
}
