# Project Requirements: Task Management API

**Project Type:** REST API  
**Technology Stack:** Python 3.11 + FastAPI + PostgreSQL  
**Purpose:** Task management system with user authentication

---

## 1. Overview

Build a RESTful API for managing tasks with user authentication. Users should be able to register, log in, and manage their personal tasks.

## 2. Technology Stack

### Backend
- **Language:** Python 3.11
- **Framework:** FastAPI
- **ORM:** SQLAlchemy
- **Migration:** Alembic

### Database
- **Database:** PostgreSQL 15
- **Connection Pool:** psycopg2

### Authentication
- **Method:** JWT (JSON Web Tokens)
- **Password Hashing:** bcrypt

### Testing
- **Framework:** pytest
- **API Testing:** httpx (FastAPI test client)

### Deployment
- **Containerization:** Docker
- **Container Orchestration:** Docker Compose

---

## 3. Features

### 3.1 User Management
- User registration with email and password
- User login returning JWT token
- Password hashing for security
- User profile retrieval

### 3.2 Task Management
- Create tasks with title, description, status, and due date
- List all tasks for logged-in user
- Filter tasks by status (pending, in_progress, completed)
- Update task details
- Delete tasks
- Mark tasks as complete

### 3.3 Security
- JWT-based authentication for protected endpoints
- Password validation (minimum 8 characters, at least one uppercase, one lowercase, one number)
- Authorization - users can only access their own tasks

---

## 4. API Endpoints

### Authentication Endpoints

#### POST /auth/register
Register a new user
- **Request:** `{ "email": "user@example.com", "password": "SecurePass123", "name": "John Doe" }`
- **Response:** `{ "id": "uuid", "email": "user@example.com", "name": "John Doe" }`

#### POST /auth/login
Login and receive JWT token
- **Request:** `{ "email": "user@example.com", "password": "SecurePass123" }`
- **Response:** `{ "access_token": "jwt-token-here", "token_type": "bearer" }`

### User Endpoints

#### GET /users/me
Get current user profile (requires authentication)
- **Response:** `{ "id": "uuid", "email": "user@example.com", "name": "John Doe" }`

### Task Endpoints

#### POST /tasks
Create a new task (requires authentication)
- **Request:** `{ "title": "Task title", "description": "Task description", "status": "pending", "due_date": "2024-12-31" }`
- **Response:** `{ "id": "uuid", "title": "...", "description": "...", "status": "pending", ... }`

#### GET /tasks
List all tasks for current user (requires authentication)
- **Query Parameters:** `?status=pending` (optional)
- **Response:** `[ { "id": "uuid", "title": "...", ... }, ... ]`

#### GET /tasks/{task_id}
Get a specific task (requires authentication)
- **Response:** `{ "id": "uuid", "title": "...", ... }`

#### PUT /tasks/{task_id}
Update a task (requires authentication)
- **Request:** `{ "title": "Updated title", "description": "...", "status": "in_progress" }`
- **Response:** `{ "id": "uuid", "title": "Updated title", ... }`

#### DELETE /tasks/{task_id}
Delete a task (requires authentication)
- **Response:** `{ "message": "Task deleted successfully" }`

---

## 5. Database Schema

### Users Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| name | VARCHAR(255) | NOT NULL |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### Tasks Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() |
| user_id | UUID | FOREIGN KEY (users.id), NOT NULL |
| title | VARCHAR(255) | NOT NULL |
| description | TEXT | |
| status | VARCHAR(50) | DEFAULT 'pending', CHECK (status IN ('pending', 'in_progress', 'completed')) |
| due_date | DATE | |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

---

## 6. Non-Functional Requirements

### Performance
- API response time < 200ms for 95th percentile
- Support up to 1000 concurrent users

### Security
- All passwords must be hashed using bcrypt
- JWT tokens expire after 24 hours
- HTTPS only in production
- Input validation on all endpoints
- SQL injection protection via ORM

### Code Quality
- Unit test coverage > 80%
- All API endpoints must have integration tests
- Code must pass linting (flake8, black)
- Type hints for all functions

### Documentation
- OpenAPI/Swagger documentation auto-generated
- README with setup instructions
- API documentation with examples

### Deployment
- Dockerized application
- Docker Compose for local development
- Environment-based configuration (.env files)
- Database migrations via Alembic

---

## 7. Project Structure

```
task-api/
├── src/
│   ├── api/
│   │   ├── auth.py
│   │   ├── tasks.py
│   │   └── users.py
│   ├── models/
│   │   ├── user.py
│   │   └── task.py
│   ├── schemas/
│   │   ├── user.py
│   │   └── task.py
│   ├── services/
│   │   ├── auth.py
│   │   └── task.py
│   ├── database.py
│   ├── config.py
│   └── main.py
├── tests/
│   ├── test_auth.py
│   ├── test_tasks.py
│   └── conftest.py
├── alembic/
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 8. Success Criteria

- ✅ All API endpoints are functional
- ✅ Authentication and authorization work correctly
- ✅ Users can only access their own tasks
- ✅ All tests pass with >80% coverage
- ✅ API documentation is complete
- ✅ Application runs in Docker
- ✅ Database migrations work correctly
