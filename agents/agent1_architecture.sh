#!/bin/bash

# Agent 1: Architecture Designer
#
# INPUT: Business Requirements Document (BRD) in markdown format (.md)
# OUTPUT: Architecture design document (architecture.md) with:
#   - Technology stack selection with versions and rationale
#   - System architecture design with diagrams
#   - Component breakdown and API design
#   - Security, scalability, and deployment planning
#   - Awaits user approval before proceeding
#
# Analyzes requirements and creates comprehensive architecture design with tech stack

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source environment variables if exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"
fi

# Default values
REQUIREMENTS_PATH=""
WORKSPACE_ROOT=""
POLICY_FILE="$SCRIPT_DIR/policies/architecture.policy.md"
OUTPUT_DIR=""
FEEDBACK=""

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
        --feedback)
            FEEDBACK="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 --requirements-path PATH --workspace-root PATH [--policy-file PATH] [--output-dir PATH] [--feedback FEEDBACK]"
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

echo "════════════════════════════════════════════════════════════════════"
echo "🏗️  Agent 1: Architecture Designer"
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "📥 INPUT:"
echo "   📄 Business Requirements Document (BRD): $REQUIREMENTS_PATH"
echo "   📋 Format: Markdown (.md)"
echo ""
echo "📤 OUTPUT:"
echo "   📄 Architecture Design: $OUTPUT_DIR/architecture.md"
echo ""
echo "⏳ AI is analyzing BRD and designing architecture..."
echo "   This will include:"
echo "   ✓ Technology stack selection (with versions & rationale)"
echo "   ✓ System architecture design (with diagrams)"
echo "   ✓ Component breakdown & API design"
echo "   ✓ Security and scalability planning"
echo "   ✓ Deployment strategy"
echo ""

# Build instruction for architecture generation
REQUIREMENTS_CONTENT=$(cat "$REQUIREMENTS_PATH")

# Build architecture context
ARCHITECTURE_CONTEXT="
═══════════════════════════════════════════════════════════════════
        🐳 DOCKER + OPEN-SOURCE STACK ARCHITECTURE
═══════════════════════════════════════════════════════════════════

CRITICAL: Design a COMPLETE, PRODUCTION-READY APPLICATION using open-source technologies with Docker.

ARCHITECTURE REQUIREMENTS:

1. **DOCKER-BASED OPEN-SOURCE STACK:**
   - **Database:** PostgreSQL 15+ (Docker container)
   - **Cache:** Redis 7+ (Docker container)
   - **Message Queue:** RabbitMQ or Redis Queue (Docker container)
   - **Object Storage:** MinIO (S3-compatible, Docker container)
   - **Search:** Elasticsearch (if needed, Docker container)
   - **Orchestration:** Docker Compose for local development and testing

2. **ENVIRONMENT FLEXIBILITY:**
   - **Local Development:** \`docker-compose up\` - all services on localhost
   - **Cloud Deployment:** Same Docker images deploy to any cloud provider
   - **Configuration:** Environment variables control behavior
   - **Portability:** NO vendor lock-in, runs anywhere

3. **MANDATORY DESIGN PATTERNS:**
   - 12-Factor App methodology
   - Environment-based configuration
   - Repository pattern for data access
   - Service layer for business logic
   - Dependency injection for testability
   - Health checks for all services

4. **LOCAL AND CLOUD COMPATIBILITY:**
   - Same codebase works locally and in cloud
   - Docker Compose for local development
   - Kubernetes manifests for cloud deployment
   - Easy migration between cloud providers
   - No proprietary cloud services

Example Architecture Pattern Required:
\`\`\`python
import os

class Config:
    # Database (PostgreSQL in Docker)
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@postgres:5432/appdb')

    # Redis Cache (Redis in Docker)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

    # Object Storage (MinIO locally, S3-compatible)
    STORAGE_ENDPOINT = os.getenv('STORAGE_ENDPOINT', 'http://minio:9000')
    STORAGE_ACCESS_KEY = os.getenv('STORAGE_ACCESS_KEY', 'minioadmin')
    STORAGE_SECRET_KEY = os.getenv('STORAGE_SECRET_KEY', 'minioadmin')
    STORAGE_BUCKET = os.getenv('STORAGE_BUCKET', 'app-storage')

    # Message Queue (RabbitMQ in Docker)
    RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@rabbitmq:5672/')

    # App Settings
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
\`\`\`

DELIVERABLE: Production-ready architecture using Docker + open-source stack for local testing and cloud deployment.

═══════════════════════════════════════════════════════════════════
"

# Add feedback section if provided
FEEDBACK_SECTION=""
if [ -n "$FEEDBACK" ]; then
    FEEDBACK_SECTION="
═══════════════════════════════════════════════════════════════════
        ⚠️  ARCHITECTURE REJECTION FEEDBACK
═══════════════════════════════════════════════════════════════════

The previous architecture design was REJECTED with the following feedback:

**FEEDBACK:**
$FEEDBACK

**ACTION REQUIRED:**
- Address ALL points mentioned in the feedback above
- Create a NEW, IMPROVED architecture design
- Make sure to incorporate the requested changes
- Explain what changes were made based on the feedback

═══════════════════════════════════════════════════════════════════
"
fi

INSTRUCTION="$POLICY_CONTENT

---

## EXECUTION CONTEXT

$ARCHITECTURE_CONTEXT

$FEEDBACK_SECTION

**REQUIREMENTS DOCUMENT:**

$REQUIREMENTS_CONTENT

---

## YOUR TASK

Analyze the above requirements and create a comprehensive architecture design.

**DELIVERABLES:**

1. Create **ONLY ONE FILE**: \`$OUTPUT_DIR/architecture.md\` following the structure defined in the policy
2. Include complete technology stack with versions and rationale
3. Design system architecture with diagrams (use ASCII art or Mermaid)
4. Define all components, APIs, database schema
5. Plan security, scalability, and deployment architecture
6. Provide complete project structure
7. End with approval notice

**CRITICAL REQUIREMENTS:**
- Be specific with technology choices (include versions)
- Explain WHY each technology was chosen
- Design for the actual requirements, not generic template
- Include realistic diagrams and schemas
- Make it ready for user review and approval
$(if [ -n "$FEEDBACK" ]; then echo "- **IMPORTANT:** Address the rejection feedback above and explain what you changed"; fi)

**STRICT FILE LIMIT:**
- You are ONLY allowed to create ONE markdown file: architecture.md
- Do NOT create any additional files (no summary files, diagram files, or reference files)
- All content MUST be in the single architecture.md file
- If the file exceeds 150 lines, use str-replace-editor to continue adding content
- Violating this rule will cause the workflow to fail

Begin architecture design now."

# Write instruction to temp file
TEMP_INSTRUCTION_FILE=$(mktemp)
echo "$INSTRUCTION" > "$TEMP_INSTRUCTION_FILE"

# Execute auggie
auggie -p -w "$WORKSPACE_ROOT" --instruction-file "$TEMP_INSTRUCTION_FILE"

# Cleanup
rm -f "$TEMP_INSTRUCTION_FILE"

echo ""
echo "════════════════════════════════════════════════════════════════════"

# Verify output
if [ ! -f "$OUTPUT_DIR/architecture.md" ]; then
    echo "❌ Error: architecture.md was not generated"
    exit 1
fi

echo "✅ Architecture design completed"
echo ""
echo "📄 Architecture document: $OUTPUT_DIR/architecture.md"
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "⚠️  APPROVAL REQUIRED"
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "Please review the architecture document before proceeding."
echo ""
echo "To approve and continue:"
echo "  python3 -m orchestrator.cli approve <workflow-id>"
echo ""
echo "To reject and provide feedback:"
echo "  python3 -m orchestrator.cli reject <workflow-id> --feedback \"Your feedback\""
echo ""
echo "════════════════════════════════════════════════════════════════════"

exit 0
