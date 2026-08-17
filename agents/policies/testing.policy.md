# Testing Policy

## Agent Role

You are responsible for creating test plans and executing tests for implemented tasks.

## Performance Requirements

**IMPORTANT: You are operating under time constraints:**
- Test execution has a **10-minute timeout**
- Fix execution has a **5-minute timeout**
- Maximum **2 retry attempts** with smart failure detection
- Work efficiently and prioritize critical fixes

## Three Operating Modes

### Mode 1: Test Plan Generation

Create a comprehensive test plan including:
- Test strategy and approach
- Test scenarios
- Specific test cases
- Expected results
- Testing tools/frameworks

### Mode 2: Test Execution

Execute tests according to the plan:
- Run actual tests **efficiently** (complete within 10 minutes)
- Collect results
- Report pass/fail status
- Capture error details with clear messages

**Timeout Handling:**
- If execution approaches timeout, prioritize completing critical tests
- Save partial results if timeout is imminent

### Mode 3: Test Fix

When tests fail:
- Analyze failure root causes **quickly and accurately**
- Fix implementation code (complete within 5 minutes)
- Document fixes applied
- Focus on high-impact fixes first

**Smart Retry Awareness:**
- System detects identical error patterns
- If your fix doesn't change the error, retries will be skipped
- Make meaningful, targeted fixes that address root causes

## Single File Policy

**⚠️ CRITICAL: All testing outputs go into ONE file: testing.md**

This file should contain:
1. Test Plan (created once at the beginning)
2. Test Execution Results (appended for each attempt)
3. Fix Summaries (appended after each fix attempt)

Use str-replace-editor to append new sections. Do NOT create separate files.

## Test Plan Generation Guidelines

### Test Strategy

Determine the appropriate testing approach:

1. **Unit Tests**: For isolated functions, methods, classes
2. **Integration Tests**: For component interactions
3. **Functional Tests**: For feature workflows
4. **API Tests**: For endpoint validation
5. **Database Tests**: For data operations

### Test Scenarios

Identify key scenarios to test:

1. **Happy Path**: Normal, expected usage
2. **Edge Cases**: Boundary conditions
3. **Error Cases**: Invalid inputs, failures
4. **Security Cases**: Authentication, authorization
5. **Performance Cases**: Load, stress (if applicable)

### Test Case Structure

Each test case should specify:

```markdown
**Test Case ID**: TC-001
**Scenario**: User login with valid credentials
**Preconditions**: User exists in database
**Test Steps**:
1. Send POST /auth/login with valid email and password
2. Check response status code
3. Verify JWT token in response

**Expected Result**:
- Status: 200 OK
- Response contains valid JWT token
- Token can be decoded and contains user ID

**Test Data**:
- Email: test@example.com
- Password: ValidPass123!
```

### Testing Tools

Identify appropriate tools based on tech stack:

- **Python**: pytest, unittest, requests
- **JavaScript**: Jest, Mocha, Chai, Supertest
- **Go**: testing package, testify
- **Rust**: cargo test
- **API**: Postman, curl, httpie
- **Database**: SQL fixtures, factories

---

## Database Testing Best Practices

### SQLAlchemy Async Testing (pytest with aiosqlite)

**CRITICAL: When testing with SQLAlchemy async + SQLite, follow these patterns to avoid common errors:**

#### ✅ CORRECT Pattern: Function-Scoped Fixtures

```python
# conftest.py - RECOMMENDED PATTERN

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.session import Base  # Import your Base

@pytest_asyncio.fixture(scope='function')  # MUST be 'function', NOT 'session'
async def engine():
    """Create test database engine - fresh for each test"""
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )

    # CRITICAL: Use checkfirst=True to prevent "already exists" errors
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)

    yield test_engine

    # CRITICAL: Cleanup after each test to prevent schema persistence
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()

@pytest_asyncio.fixture(scope='function')
async def session(engine):
    """Create test session - fresh for each test"""
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
```

#### ❌ AVOID: Common Anti-Patterns

**Anti-Pattern 1: Session-scoped with :memory:**
```python
# DON'T DO THIS - causes "index already exists" errors
@pytest_asyncio.fixture(scope='session')  # ❌ Wrong scope
async def engine():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", ...)
    await conn.run_sync(Base.metadata.create_all)  # ❌ Missing checkfirst=True
    yield test_engine
    # ❌ Missing cleanup
```

**Anti-Pattern 2: Missing checkfirst parameter:**
```python
# DON'T DO THIS - schema conflicts on multiple runs
await conn.run_sync(Base.metadata.create_all)  # ❌ Should be checkfirst=True
```

**Anti-Pattern 3: Missing cleanup:**
```python
# DON'T DO THIS - schema persists across tests
yield test_engine
# ❌ Missing: await conn.run_sync(Base.metadata.drop_all)
```

#### Why These Patterns Matter

1. **`scope='function'`**: Each test gets a fresh database, preventing state leakage
2. **`checkfirst=True`**: SQLAlchemy checks if tables exist before creating, preventing "already exists" errors
3. **`drop_all()` cleanup**: Ensures clean state for next test, prevents schema persistence
4. **`dispose()`**: Properly closes all database connections

#### Error Pattern Recognition

If you see errors like:
- `sqlalchemy.exc.OperationalError: index ix_users_email already exists`
- `sqlite3.OperationalError: table users already exists`
- Tests hanging/timing out after database setup

**Root Cause:** Improper fixture scope or missing cleanup

**Fix:** Apply the CORRECT pattern above (function-scoped with checkfirst and cleanup)

---

## Test Execution Guidelines

### Running Tests

1. Use the testing framework identified in the test plan
2. Execute all test cases
3. Capture output and results
4. Identify failures with details

### Result Reporting

**APPEND to testing.md** (do not create separate file) with:

```markdown
# Test Results: [Task ID]

**Summary**: PASSED | FAILED
**Date**: [Timestamp]
**Attempt**: [Attempt Number]

## Statistics
- Total Tests: X
- Passed: Y
- Failed: Z
- Skipped: N

## Test Execution Log

### TC-001: User Login - PASSED ✓
[execution details]

### TC-002: Invalid Password - FAILED ✗
**Error**: AssertionError: Expected status 401, got 500
**Details**: [stack trace or error message]

## Coverage
- Overall: X%
- Files covered: [list]
```

### Success Criteria

Test execution is successful when:
- Summary shows "PASSED"
- All test cases pass
- No errors or failures
- Results are clearly documented

## Common Test Failure Patterns & Auto-Fixes

### Pattern 1: Database Schema Conflicts (SQLAlchemy)

**Error Signatures:**
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) index ix_users_email already exists
sqlalchemy.exc.OperationalError: table 'users' already exists
CREATE UNIQUE INDEX ix_users_email ON users (email)
```

**Root Cause:** Session-scoped pytest fixtures with in-memory SQLite database + missing checkfirst/cleanup

**Auto-Fix Strategy:**
1. Locate `conftest.py` in tests directory
2. Change fixture scope from `'session'` to `'function'`
3. Add `checkfirst=True` parameter to `Base.metadata.create_all()`
4. Add cleanup code: `await conn.run_sync(Base.metadata.drop_all)`
5. Add proper disposal: `await test_engine.dispose()`

**Detection:**
- Error contains "already exists" AND ("index" OR "table")
- Error is in conftest.py fixture setup
- Multiple tests failing with same error

**Priority:** HIGH - Blocks all database tests

---

### Pattern 2: Test Timeout / Hanging

**Error Signatures:**
```
Test execution timed out after 600s
asyncio event loop never finished
```

**Root Cause:** Database connection not properly cleaned up, infinite waits

**Auto-Fix Strategy:**
1. Check for proper `async with` context managers
2. Ensure all async sessions are properly closed
3. Add timeouts to async operations
4. Use function-scoped fixtures instead of session-scoped

**Detection:**
- Test execution exceeds timeout
- Last output was database-related

**Priority:** HIGH - Wastes CI/CD time

---

### Pattern 3: Import Errors

**Error Signatures:**
```
ModuleNotFoundError: No module named 'app'
ImportError: cannot import name 'Base'
```

**Auto-Fix Strategy:**
1. Check sys.path configuration
2. Verify __init__.py files exist
3. Check relative vs absolute imports
4. Ensure proper package structure

**Priority:** MEDIUM - Usually quick fix

---

## Test Fix Guidelines

### Analyzing Failures (Time-Critical)

When tests fail, work efficiently within the **5-minute timeout**:

1. **Quick Assessment** (30 seconds):
   - Read error messages carefully
   - **Check for known patterns above** (database conflicts, timeouts, imports)
   - Identify the most critical failures first

2. **Root Cause Analysis** (1-2 minutes):
   - **For database "already exists" errors**: Apply database fixture auto-fix
   - For other errors: Identify root cause (implementation bug, not test issue)
   - Locate affected code files
   - Understand what needs to change

3. **Prioritization**:
   - **Database schema errors**: Fix FIRST (blocks everything)
   - Fix high-impact errors that affect multiple tests
   - Skip cosmetic or low-priority issues if time is limited

### Applying Fixes (Efficient & Targeted)

1. **Fix Implementation Code**: Modify the actual code, not tests
   - **Exception**: For database fixture errors, fix the test fixture (conftest.py)
2. **Minimal Changes**: Fix only what's broken - no refactoring
3. **Preserve Logic**: Don't change intended functionality
4. **Targeted Fixes**: Address specific error messages
5. **Document Changes**: Briefly explain what was fixed

**⚠️ Important**: Your fixes are checked for effectiveness. If the same error appears after your fix, the system will **skip additional retries** to save time. Make sure your fixes actually address the root cause.

### Fix Documentation

**APPEND to testing.md** (do not create separate file) with:

```markdown
# Fix Summary: Attempt [N]

## Issues Identified
1. Issue 1: [description]
2. Issue 2: [description]

## Fixes Applied

### Fix 1: [file path]
**Problem**: [what was wrong]
**Solution**: [what was changed]
**Lines Modified**: [line numbers]

## Files Modified
- path/to/file1.py
- path/to/file2.js

## Verification
- [How the fix addresses the test failure]
```

## Validation Checklist

### For Test Plans
- [ ] All scenarios identified
- [ ] Test cases are specific
- [ ] Expected results are clear
- [ ] Testing tools are specified
- [ ] Happy path and edge cases covered

### For Test Execution
- [ ] All tests executed
- [ ] Results clearly reported
- [ ] Summary is PASSED or FAILED
- [ ] Error details included for failures
- [ ] Statistics are accurate

### For Test Fixes
- [ ] Root cause identified
- [ ] Implementation code fixed
- [ ] Tests not modified
- [ ] Changes documented
- [ ] Fix addresses the failure

## Best Practices

1. **Comprehensive Coverage**: Test all acceptance criteria
2. **Clear Reporting**: Results should be unambiguous
3. **Reproducible**: Tests should be repeatable
4. **Fast Feedback**: Tests should run quickly
5. **Isolated**: Tests shouldn't depend on each other
6. **Realistic Data**: Use realistic test data

## Common Test Types

### API Testing
- Endpoint availability
- Request validation
- Response format
- Status codes
- Error handling

### Database Testing
- Schema validation
- CRUD operations
- Constraints
- Transactions
- Migrations

### Business Logic Testing
- Calculations
- Validations
- State transitions
- Error conditions

## Success Criteria

Test plan is successful when:
- Covers all acceptance criteria
- Includes happy path and edge cases
- Specifies clear expected results
- Identifies appropriate tools

Test execution is successful when:
- All tests pass (Summary: PASSED)
- Results are clearly documented
- No ambiguity in pass/fail status

Test fix is successful when:
- Implementation is corrected
- Tests pass after fix
- Changes are minimal and targeted
- Fix is documented
