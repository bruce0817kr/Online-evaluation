# Claude Code Project Guidelines

This document provides guidelines for using Claude Code (claude.ai/code) when working with code in this repository. All team members must adhere to these rules to ensure token efficiency and systematic development.

## Port Management

**Important**: All ports must be dynamically allocated through the **Universal Port Manager (UPM)**. Do not hardcode ports in code or configuration files. UPM provides ports via the `.env` file or other configuration files (e.g., `ports.json`, `set_ports.sh`). For example:
- Backend: Use the `BACKEND_PORT` environment variable.
- Frontend: Use the `PORT` environment variable.
- UPM Commands: Run `python -m universal_port_manager --project online-evaluation allocate frontend backend mongodb redis` to allocate ports and `generate` to create configuration files.

## Architecture Overview

This project is a full-stack **Online Evaluation System** built with the following technologies:

### Backend (FastAPI + MongoDB)
- **Framework**: FastAPI with async/await pattern
- **Database**: MongoDB with Motor (async driver)
- **Authentication**: JWT tokens with role-based access (Admin, Manager, Evaluator)
- **File Storage**: Local uploads directory with PDF/Excel support
- **Key Files**:
  - `backend/server.py` - Main FastAPI application with all API endpoints
  - `backend/models.py` - Pydantic models and data schemas
  - `backend/security.py` - Authentication, authorization, password hashing
  - `backend/export_utils.py` - PDF/Excel export functionality

### Frontend (React)
- **Framework**: React 19 with functional components and hooks
- **Styling**: CSS3 + Tailwind CSS
- **State Management**: Local component state with useEffect/useState
- **PDF Handling**: react-pdf with pdfjs-dist for document viewing
- **Key Files**:
  - `frontend/src/App.js` - Main application component with routing logic
  - `frontend/src/components/TemplateManagement.js` - Template CRUD operations
  - `frontend/src/components/EvaluationManagement.js` - Evaluation workflow

## Development Commands

### Backend Development
```bash
cd backend
python -m uvicorn server:app --reload --port ${BACKEND_PORT}  # BACKEND_PORT set by UPM
```

### Frontend Development
```bash
cd frontend
npm install
npm start  # PORT set by UPM in .env, proxies to backend on ${BACKEND_PORT}
```

### Universal Port Manager (Smart Deployment)
```bash
# Smart deployment with automatic port conflict resolution
deploy_with_port_manager.bat

# CLI usage for manual port management
python -m universal_port_manager --project online-evaluation allocate frontend backend mongodb redis
python -m universal_port_manager --project online-evaluation generate
python -m universal_port_manager --project online-evaluation start
python -m universal_port_manager --project online-evaluation status

# Integration example
python integration_example.py
```

### Testing Commands
```bash
# Playwright E2E tests
npm test                    # Run all tests, using ports assigned by UPM
npm run test:headed        # Run with browser UI
npm run test:debug         # Debug mode
npm run test:ui            # Test runner UI
npm run test:auth          # Authentication tests only
npm run test:workflow      # Workflow tests only

# Install Playwright browsers
npm run install:browsers
```

### Docker Development
```bash
# Development environment
npm run start:dev           # Uses docker-compose.dev.yml
docker-compose up -d        # Standard Docker setup

# Production environment
npm run start:prod          # Uses docker-compose.prod.yml
```

## Key Architecture Patterns

### API Structure
- **RESTful Endpoints**: `/api/auth/*`, `/api/templates/*`, `/api/evaluations/*`
- **File Operations**: `/api/files/*` with authentication required
- **Export System**: Individual and bulk exports with ZIP packaging
- **WebSocket Support**: Real-time updates for evaluation progress

### Authentication Flow
1. Login via `/api/auth/login` returns JWT token
2. Token required in `Authorization: Bearer <token>` header
3. Role-based permissions: Admin > Manager > Evaluator
4. Current user info available at `/api/auth/me`

### Database Collections
- `users` - User accounts with role-based access
- `companies` - Organization/company groupings
- `projects` - Evaluation projects with team assignments
- `templates` - Evaluation criteria and scoring templates
- `evaluations` - Completed evaluation submissions
- `files` - File metadata with upload tracking

### Export System
- **Individual Exports**: PDF/Excel per evaluation
- **Bulk Exports**: ZIP files with multiple evaluations
- **Korean Font Support**: Proper rendering in PDF reports
- **Template-based**: Uses ReportLab for PDFs, OpenPyXL for Excel

## Testing Strategy

### E2E Test Structure (`tests/e2e/`)
- `auth.spec.js` - Login/logout, role verification
- `system.spec.js` - Full system integration tests
- `ui.spec.js` - UI component and interaction tests
- `workflow.spec.js` - Complete user workflow scenarios

### Test Environment
- **Frontend**: Port assigned by UPM (e.g., 3001)
- **Backend**: Port assigned by UPM (e.g., 8080)
- **Database**: MongoDB with test data seeding
- **Screenshots**: Automatic capture on test failures

## Common Development Tasks

### Adding New API Endpoints
1. Add route to `backend/server.py`
2. Create Pydantic models in `backend/models.py`
3. Add authentication checks using `get_current_user` dependency
4. Update frontend API client in `frontend/src/services/apiClient.js`

### Frontend Component Development
1. Create component in `frontend/src/components/`
2. Import and use in `App.js` routing logic
3. Follow existing patterns for API calls and state management
4. Use CSS classes following established naming conventions

### Database Schema Changes
1. Update models in `backend/models.py`
2. Add migration logic if needed (currently using direct MongoDB operations)
3. Update test data creation scripts in `scripts/`

## Environment Configuration

### Required Environment Variables
**Note**: All port-related variables are set by UPM. Do not hardcode port values.

#### Backend (.env)
```
MONGO_URL=mongodb://admin:password123@localhost:27017/online_evaluation
JWT_SECRET=your-secret-key
UPLOAD_DIR=./uploads
CORS_ORIGINS=http://localhost:<frontend_port>  # <frontend_port> set by UPM, e.g., 3000
BACKEND_PORT=<backend_port>  # <backend_port> set by UPM, e.g., 8080
```

#### Frontend (.env)
```
REACT_APP_BACKEND_URL=http://localhost:<backend_port>  # <backend_port> set by UPM, e.g., 8080
PORT=<frontend_port>  # <frontend_port> set by UPM, e.g., 3000
```

### Development vs Production
- **Development**: Uses `docker-compose.dev.yml` with hot reload
- **Production**: Uses `docker-compose.prod.yml` with optimized builds
- **Port Mapping**: UPM dynamically allocates ports for frontend, backend, MongoDB, and Redis

## Troubleshooting

### Backend Issues
- **Database Connection**: Ensure MongoDB is running and accessible
- **JWT Errors**: Check `JWT_SECRET` environment variable
- **File Upload Issues**: Verify uploads directory permissions
- **CORS Errors**: Check `CORS_ORIGINS` configuration, ensure UPM set correct ports

### Frontend Issues
- **Proxy Errors**: Ensure backend is running on UPM-assigned port
- **PDF Viewing**: Check pdfjs-dist worker configuration
- **Build Failures**: Clear node_modules and run `npm install`

### Test Issues
- **Playwright Browser Issues**: Run `npm run install:browsers`
- **Port Conflicts**: Use UPM for automatic resolution
- **Test Data**: Use scripts in `scripts/` to reset test data

### Universal Port Manager Issues
- **Dependency Errors**: Install with `pip install click psutil pyyaml`
- **Permission Errors**: Run as administrator for system port scanning
- **Config Conflicts**: Clear `.port-manager/` directory and regenerate

## 🚀 Universal Port Manager Integration

This project includes a **Universal Port Manager (UPM)** system that automatically handles port conflicts and enables multiple projects to run simultaneously without interference.

### Key Features
- **🔍 Intelligent Port Scanning**: Detects system, Docker, and process port usage
- **🎲 Automatic Port Allocation**: Service-type-based port ranges with conflict avoidance
- **📦 Project Grouping**: Project-specific port management with persistence
- **🐳 Docker Integration**: Automatic Docker Compose file generation
- **⚙️ Configuration Generation**: .env, bash, python, json format support
- **🌐 Global/Local Modes**: System-wide or project-local management

### Usage Patterns

#### Basic Usage
```python
from universal_port_manager import PortManager

# Initialize for online-evaluation project
pm = PortManager(project_name="online-evaluation")

# Allocate ports for required services
ports = pm.allocate_services(['frontend', 'backend', 'mongodb', 'redis'])

# Generate all configuration files
pm.generate_all_configs()

# Start services
pm.start_services()
```

#### CLI Usage
```bash
# Allocate ports
python -m universal_port_manager --project online-evaluation allocate frontend backend mongodb redis

# Generate configuration files
python -m universal_port_manager --project online-evaluation generate

# Check status
python -m universal_port_manager --project online-evaluation status

# Start services
python -m universal_port_manager --project online-evaluation start
```

#### Multiple Project Support
```python
# online-evaluation project
eval_pm = PortManager(project_name="online-evaluation")
eval_ports = eval_pm.allocate_services(['frontend', 'backend', 'mongodb', 'redis'])

# newsscout project (runs simultaneously without conflicts)
news_pm = PortManager(project_name="newsscout")
news_ports = news_pm.allocate_services(['frontend', 'backend', 'postgresql', 'redis'])

# Both projects can run simultaneously!
```

### Generated Files
UPM automatically creates:
```
project-directory/
├── docker-compose.yml          # Main Docker Compose file
├── docker-compose.override.yml # Development overrides with allocated ports
├── .env                        # Environment variables
├── set_ports.sh               # Bash environment script
├── port_config.py          # Python configuration
├── ports.json                 # JSON configuration
├── start.sh                   # Service startup script
└── .port-manager/             # Port manager settings
    ├── port_allocations.json  # Port allocation history
    └── service_types.json     # Service type definitions
```

### Deployment Integration
The `deploy_with_port_manager.bat` script replaces the original deployment script with intelligent port management:
1. **System Scanning**: Scans all active ports (system, Docker, processes)
2. **Smart Allocation**: Assigns ports based on service types and availability
3. **Configuration Generation**: Creates all necessary config files
4. **Docker Integration**: Builds and starts services with allocated ports
5. **Health Checking**: Verifies service startup and connectivity

### Service Types Supported
- **Frontend**: React (3000), Vue (8080), Angular (4200), Next.js (3000)
- **Backend**: FastAPI (8000), Express (3000), Django (8000), Flask (5000)
- **Database**: MongoDB (27017), PostgreSQL (5432), MySQL (3306), Redis (6379)
- **Infrastructure**: Nginx (80), Elasticsearch (9200), Prometheus (9090), Grafana (3000)

### Multi-Project Scenarios
This system supports running multiple projects simultaneously, such as:
- **online-evaluation** (this project)
- **newsscout** (another project)
- Any other projects

All can run without port conflicts.

### Migration from Legacy Deployment
UPM can migrate existing hardcoded ports while maintaining compatibility:
```python
# Legacy ports are preserved when possible
legacy_ports = {'frontend': 3000, 'backend': 8080, 'mongodb': 27017}
pm = PortManager(project_name="online-evaluation")
ports = pm.allocate_services(services, preferred_ports=legacy_ports)
```

## 🎯 Development Principles

### TDD Basic Cycle
1. **RED**: Write failing test first
2. **GREEN**: Minimal code to pass test
3. **REFACTOR**: Improve and optimize code

### Clean Architecture
- **Single Responsibility**: One class, one reason to change
- **Dependency Inversion**: Depend on abstractions, not concretions
- **Interface Segregation**: Client-specific interfaces

### Security Priorities
- **Input Validation**: Sanitize all user inputs
- **Output Encoding**: Prevent XSS attacks
- **Least Privilege**: Minimum required permissions
- **Error Handling**: No sensitive information leakage

### Code Quality Standards
- **Type Safety**: Use Pydantic for Python, strict validation for JS
- **Test Coverage**: Maintain 90%+ coverage
- **Performance**: Target Lighthouse score 95+
- **Readability**: Self-documenting, clear code

## 🔒 Security Checklist
- MongoDB injection prevention (parameterized queries)
- XSS prevention (output encoding)
- CSRF prevention (token validation)
- Authentication/authorization verification

## 🚀 Performance Targets
- **Build Time**: < 30 seconds
- **Test Execution**: < 10 seconds
- **Page Load**: < 1.2 seconds
- **Lighthouse Score**: 95+

## Token Efficiency Optimization
- **Reusable Modules**: Modularize common functionality in `utils.py`
- **Efficient Data Processing**: Use Pydantic models for input/output validation
- **Minimized API Calls**: Use caching to reduce unnecessary calls
  ```python
  from functools import lru_cache
  @lru_cache(maxsize=100)
  def cached_claude_call(prompt: str) -> str:
      return claude_client.conversation(prompt)
  ```