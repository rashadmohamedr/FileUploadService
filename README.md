# File Upload Service 📁

A production-ready RESTful API built with FastAPI for secure file upload, management, and user authentication. This service provides a complete backend solution for handling file storage with user management capabilities.

## 🚀 Features

- **User Authentication**
  - User registration with email validation
  - Secure login system
  - Password hashing using bcrypt
  - JWT token-based authentication (ready for implementation)

- **File Management**
  - Upload files with automatic UUID-based naming
  - Download files by ID
  - List all files with pagination
  - Delete files (removes from both disk and database)
  - Content type detection and preservation
  - File ownership tracking

- **Security**
  - Password hashing with bcrypt
  - SQL injection protection via SQLAlchemy ORM
  - Environment-based configuration
  - Secure file path handling

- **Database**
  - SQLAlchemy ORM with SQLite (easily switchable to PostgreSQL/MySQL)
  - Automatic database initialization
  - Relational data model (Users ↔ Files)

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Database**: SQLAlchemy (SQLite default, configurable)
- **Authentication**: Passlib with bcrypt
- **Validation**: Pydantic v2
- **Server**: Uvicorn
- **Containerization**: Docker & Docker Compose
- **File Processing**: Pillow

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

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Register a new user |
| POST | `/auth/login` | Login with email and password |

### File Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/file/upload` | Upload a new file |
| GET | `/file/download/{file_id}` | Download a file by ID |
| GET | `/file/` | List all files (with pagination) |
| DELETE | `/file/{file_id}` | Delete a file |

### Admin (Placeholder)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/dashboard` | Admin dashboard endpoint |

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

### Upload a File

```bash
curl -X POST "http://localhost:8000/file/upload" \
  -F "file=@/path/to/your/file.pdf" \
  -F "owner_id=1"
```

### Download a File

```bash
curl -X GET "http://localhost:8000/file/download/1" \
  --output downloaded_file.pdf
```

### List Files

```bash
curl -X GET "http://localhost:8000/file/?skip=0&limit=10"
```

### Delete a File

```bash
curl -X DELETE "http://localhost:8000/file/1"
```

## 🏗️ Project Structure

```
FileUploadService/
├── app/
│   ├── core/                 # Core functionality
│   │   ├── config.py         # Configuration settings
│   │   └── security.py       # Password hashing utilities
│   ├── db/                   # Database configuration
│   │   └── database.py       # SQLAlchemy setup
│   ├── models/               # SQLAlchemy models
│   │   ├── user.py           # User model
│   │   └── file.py           # File model
│   ├── schemas/              # Pydantic schemas
│   │   ├── user.py           # User schemas
│   │   └── file.py           # File schemas
│   ├── routers/              # API endpoints
│   │   ├── auth_router.py    # Authentication routes
│   │   └── file_router.py    # File management routes
│   ├── services/             # Business logic
│   │   ├── auth_service.py   # Authentication service
│   │   └── file_service.py   # File handling service
│   ├── internal/             # Internal/admin routes
│   │   └── admin.py          # Admin endpoints
│   ├── dependencies.py       # Dependency injection
│   └── main.py               # Application entry point
├── uploads/                  # Uploaded files storage
├── .env                      # Environment variables
├── docker-compose.yaml       # Docker Compose configuration
├── Dockerfile                # Docker image definition
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

## 🔐 Security Considerations

- **Password Storage**: Passwords are hashed using bcrypt before storage
- **File Storage**: Files are saved with UUID-based names to prevent path traversal attacks
- **Environment Variables**: Sensitive configuration is stored in `.env` file (not committed to git)
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **Input Validation**: Pydantic validates all input data

**Note**: JWT token authentication is configured but not yet implemented in the auth endpoints. The token fields in responses are currently empty placeholders.

## 🚧 Roadmap

- [ ] Implement JWT token generation and validation
- [ ] Add protected routes with authentication middleware
- [ ] Implement file size limits
- [ ] Add file type restrictions
- [ ] User profile management endpoints
- [ ] File sharing between users
- [ ] Admin dashboard functionality
- [ ] Database migration support (Alembic)
- [ ] Unit and integration tests
- [ ] PostgreSQL support
- [ ] S3/Cloud storage integration
- [ ] File versioning
- [ ] Thumbnails for images

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 👤 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [Your LinkedIn](https://linkedin.com/in/yourprofile)

## 🙏 Acknowledgments

- FastAPI for the amazing framework
- SQLAlchemy for robust ORM functionality
- The open-source community

---

**Note**: This is a portfolio project demonstrating backend development skills with FastAPI, SQLAlchemy, Docker, and RESTful API design principles.