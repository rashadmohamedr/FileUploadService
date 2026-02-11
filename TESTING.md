# Test Configuration and Running Guide

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories

#### Unit Tests Only
```bash
pytest tests/unit/
```

#### Integration Tests Only
```bash
pytest tests/integration/
```

#### E2E Tests Only
```bash
pytest tests/e2e/
```

### Run Specific Test Files
```bash
pytest tests/unit/test_validators.py
pytest tests/integration/test_auth_router.py
```

### Run Tests with Coverage
```bash
pytest --cov=app --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`

### Run Tests with Verbose Output
```bash
pytest -v
```

### Run Tests and Stop at First Failure
```bash
pytest -x
```

### Run Tests Matching a Pattern
```bash
pytest -k "test_upload"
```

### Show Print Statements
```bash
pytest -s
```

### Run Tests in Parallel (Faster)
```bash
pytest -n auto
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_validators.py  # File validation logic
│   ├── test_security.py    # Password hashing, JWT
│   ├── test_auth_service.py # Authentication service
│   └── test_file_service.py # File service logic
├── integration/             # Integration tests (with DB)
│   ├── test_auth_router.py # Auth API endpoints
│   └── test_file_router.py # File API endpoints
└── e2e/                     # End-to-end tests
    └── test_user_workflows.py # Complete user journeys
```

## Test Coverage Goals

- **Unit Tests**: 80%+ coverage of business logic
- **Integration Tests**: All API endpoints tested
- **E2E Tests**: Critical user workflows tested

## Best Practices Implemented

### 1. **Test Isolation**
- Each test is independent
- Database is reset between tests
- Temporary files are cleaned up

### 2. **Realistic Test Data**
- Using Faker library for realistic data
- Testing edge cases and boundary conditions
- Testing with various file types and sizes

### 3. **Security Testing**
- SQL injection attempts
- XSS attacks
- Path traversal attacks
- Authorization checks

### 4. **Performance Considerations**
- Tests run in under 30 seconds
- Use in-memory SQLite for speed
- Parallel execution supported

### 5. **Clear Test Names**
- Descriptive test names explain what is being tested
- Organized into test classes by feature
- Documentation for complex scenarios

## Continuous Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Troubleshooting

### Tests Failing?

1. **Database Issues**: Delete `test.db` file
2. **Import Errors**: Run `pip install -r requirements.txt`
3. **Permission Errors**: Check uploads directory permissions
4. **Slow Tests**: Run with `-n auto` for parallel execution

### Common Issues

#### "ModuleNotFoundError"
```bash
pip install -e .
```

#### "Database is locked"
- Close other processes using the test database
- Delete `test.db` file

#### "Permission denied" on uploads/
```bash
chmod +x uploads/
```

## Debugging Tests

### Run Single Test with Debugger
```python
pytest tests/unit/test_validators.py::TestSanitizeFilename::test_sanitize_normal_filename --pdb
```

### Print Test Output
```bash
pytest -s tests/unit/test_validators.py
```

## Quality Metrics

Current test suite provides:
- ✅ Comprehensive unit test coverage
- ✅ Full API endpoint testing
- ✅ Real-world user workflow validation
- ✅ Security vulnerability testing
- ✅ Performance regression testing
- ✅ Database integrity testing
- ✅ File handling edge cases

##Additional Notes

- Tests use production-like configuration
- Follows pytest best practices
- Includes parametrized tests for efficiency
- Tests are well-documented
- Fixtures are reusable across test modules
