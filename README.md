# File Upload Service 📁

A production-ready RESTful API built with FastAPI for secure file upload, management, and user authentication. This service provides a complete backend solution for handling file storage with user management capabilities.

## 🚀 Features

- **User Authentication**
  - User registration with email validation
  - Secure login system
  - Password hashing using bcrypt
  - JWT token-based authentication with access tokens
  - Protected endpoints with user authentication

- **File Management**
  - Upload files with automatic UUID-based naming
  - Download files by ID with ownership verification
  - List user's own files
  - Delete files with ownership checks (removes from both disk and database)
  - Content type detection and preservation
  - File ownership tracking and authorization

- **Security**
  - JWT token authentication and authorization
  - Password hashing with bcrypt
  - SQL injection protection via SQLAlchemy ORM
  - Environment-based configuration
  - Secure file path handling
  - User ownership verification for all file operations

- **Database**
  - SQLAlchemy ORM with SQLite (easily switchable to PostgreSQL/MySQL)
  - Automatic database initialization
  - Relational data model with proper foreign keys (Users ↔ Files)

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Database**: SQLAlchemy (SQLite default, PostgreSQL recommended for production)
- **Authentication**: JWT (JSON Web Tokens) with Passlib/bcrypt
- **Validation**: Pydantic v2
- **Server**: Uvicorn
- **Containerization**: Docker & Docker Compose
- **File Processing**: Pillow, python-magic (optional)

## 📋 Prerequisites

- Python 3.12+
- Docker & Docker Compose (for containerized deployment)
- pip

## 🔧 Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd FileUploadService
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   DATABASE_URL=sqlite:///./files.db
   UPLOAD_DIR=uploads/
   SECRET_KEY=your-secret-key-here-change-in-production
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

   The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once the server is running, visit:
- **Interactive API docs (Swagger)**: `http://localhost:8000/docs`
- **Alternative API docs (ReDoc)**: `http://localhost:8000/redoc`

## 🔌 API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/signup` | Register a new user | No |
| POST | `/auth/login` | Login and receive JWT token | No |

### File Operations (All require authentication)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/files/upload` | Upload a new file | Yes |
| GET | `/files/{file_id}/download` | Download your file by ID | Yes |
| GET | `/files/` | List all your files | Yes |
| DELETE | `/files/{file_id}` | Delete your file | Yes |

### Admin (Placeholder)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/admin/dashboard` | Admin dashboard endpoint | Yes (Admin) |

## 📝 Usage Examples

### Register a User

```bash
curl -X POST "http://localhost:8000/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepassword123"
  }'
```

### Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepassword123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Upload a File (with authentication)

```bash
curl -X POST "http://localhost:8000/files/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/your/file.pdf"
```

### Download a File

```bash
curl -X GET "http://localhost:8000/files/1/download" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  --output downloaded_file.pdf
```

### List Your Files

```bash
curl -X GET "http://localhost:8000/files/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Delete a File

```bash
curl -X DELETE "http://localhost:8000/files/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🏗️ Project Structure

```
FileUploadService/
├── app/
│   ├── core/                 # Core functionality
│   │   ├── config.py         # Configuration settings
│   │   ├── security.py       # Password hashing & JWT utilities
│   │   └── validators.py     # File validation (planned)
│   ├── db/                   # Database configuration
│   │   └── database.py       # SQLAlchemy setup
│   ├── models/               # SQLAlchemy models
│   │   ├── user.py           # User model
│   │   └── file.py           # File model with foreign keys
│   ├── schemas/              # Pydantic schemas
│   │   ├── user.py           # User schemas
│   │   └── file.py           # File schemas
│   ├── routers/              # API endpoints
│   │   ├── auth_router.py    # Authentication routes
│   │   └── file_router.py    # File management routes (protected)
│   ├── services/             # Business logic
│   │   ├── auth_service.py   # Authentication & JWT service
│   │   └── file_service.py   # File handling service
│   ├── internal/             # Internal/admin routes
│   │   └── admin.py          # Admin endpoints (planned)
│   ├── dependencies.py       # JWT validation & user injection
│   └── main.py               # Application entry point
├── uploads/                  # Uploaded files storage
├── .env                      # Environment variables
├── .env.example              # Environment variables template (planned)
├── docker-compose.yaml       # Docker Compose configuration
├── Dockerfile                # Docker image definition
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

## 🔐 Security Considerations

- **JWT Authentication**: All file operations require valid JWT tokens
- **Password Storage**: Passwords are hashed using bcrypt before storage
- **File Ownership**: Users can only access/modify their own files
- **File Storage**: Files are saved with UUID-based names to prevent path traversal attacks
- **Environment Variables**: Sensitive configuration is stored in `.env` file (not committed to git)
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **Input Validation**: Pydantic validates all input data

## 🚧 Roadmap

### ✅ Completed Features (`main`)
- User registration and authentication
- JWT token generation and validation
- Protected file routes with authentication middleware
- User ownership verification for file operations
- Database models with proper foreign key relationships
- Schema consistency (snake_case naming)
- Basic file upload/download/delete functionality

### 🔄 In Progress (Current Sprint) (`feature/file-security-validation`)
- **File Security & Validation** <--
  - File size limits and validation
  - File type/extension whitelisting and blacklisting
  - Filename sanitization (prevent directory traversal)
  - Magic number validation (content type verification)
  - Optional virus scanning with ClamAV integration
  - Enhanced ownership checks in all endpoints

### 📋 Planned Features

#### High Priority (`feature/enhanced-error-handling`)
- **New Features**
  - Replace generic exception handlers with specific error types
  - Add structured logging (JSON format)
  - Request ID tracking for debugging

- **Production-Ready Features** (`feature/production-ready`)
  - Create `.env.example` template
  - CORS configuration in `main.py`
  - Health check endpoint (`/health`)
  - API versioning (e.g., `/api/v1/`)
  - Request rate limiting (prevent abuse)

#### Medium Priority (`feature/testing-and-docs`)
- **Testing & Documentation**
  - Unit tests with pytest
  - Integration tests for API endpoints
  - Test coverage reporting
  - Enhanced OpenAPI documentation with examples
  - Postman/Insomnia collection

- **Admin Dashboard** (`feature/admin-dashboard`)
  - User management (list, disable, delete users)
  - File analytics (storage usage, upload trends)
  - Storage metrics and monitoring
  - Role-based access control (RBAC)
  - Audit logging

- **User Features** (`feature/user-features`)
  - User profile management endpoints
  - Password reset functionality
  - Email verification for new accounts
  - Account deletion (with cascading file cleanup)

#### New Features

- **Analytics Dashboard API** (`feature/analytics-dashboard`)
  - Receive data from clients
  - Store it in PostgreSQL
  - Serve aggregated stats with caching (Redis)
  - Tests with pytest

- **API Gateway** (`feature/api-gateway`)
  - Combine multiple microservices (auth, payments, file logic)
  - Implement rate limiting
  - API key management for external clients

### 🔧 Planned Code Fixes

#### High Priority (`feature/enhanced-error-handling`)
- **Code Fixes**
  - Implement proper database rollback mechanisms
  - Consistent error response formats across all endpoints

- **Production-Ready Fixes** (`feature/production-ready`)
  - Fix `requirments.txt` → `requirements.txt` typo
  - Database migrations with Alembic

- **Docker & Deployment Improvements** (`feature/docker-deployment`)
  - Add PostgreSQL to `docker-compose.yaml`
  - Multi-stage Docker builds (smaller images)
  - Container health checks
  - Volume persistence for database and uploads
  - Environment-specific configurations (dev/staging/prod)

### Future Enhancements

#### Scalability & Performance (`feature/scalability`)
- Migrate from SQLite to PostgreSQL for production
- Cloud storage integration (AWS S3, Azure Blob, Google Cloud Storage)
- Signed URLs for secure downloads
- CDN integration for file delivery
- Database connection pooling
- Redis caching layer

#### Advanced File Features (`feature/advanced-file-features`)
- File sharing between users
- File versioning and history
- Thumbnail generation for images
- Bulk file operations
- ZIP archive download for multiple files
- File search and filtering
- Metadata extraction and indexing

#### Monitoring & Observability (`feature/monitoring`)
- Prometheus metrics export
- Grafana dashboards
- APM integration (DataDog, New Relic, or similar)
- Error tracking (Sentry)
- Uptime monitoring

### 🤔 Under Consideration
- WebSocket support for real-time upload progress
- GraphQL API alongside REST
- Multi-tenancy support (organizations/workspaces)
- Client SDKs (Python, JavaScript, Go)
- File encryption at rest
- Compliance features (GDPR, data retention policies)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 👤 Author

**Your Name**
- GitHub: [@rashadmohamedr](https://github.com/rashadmohamedr)
- LinkedIn: [LinkedIn](https://www.linkedin.com/in/rashad-mohamed-5ba667221)

## 🙏 Acknowledgments

- FastAPI for the amazing framework
- SQLAlchemy for robust ORM functionality
- The open-source community

---

**Note**: This is a portfolio project demonstrating backend development skills with FastAPI, SQLAlchemy, Docker, JWT authentication, and RESTful API design principles.