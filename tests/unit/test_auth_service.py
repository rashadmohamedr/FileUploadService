"""
Unit tests for authentication service.
Testing user creation and authentication logic with database interactions.
"""
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.services.auth_service import create_user, authenticate_user, update_last_login
from app.schemas.user import UserCreate, UserLogin
from app.models.user import User
from app.core.security import pwd_context
from datetime import datetime


class TestCreateUser:
    """Test user creation functionality."""
    
    def test_create_user_success(self, db_session: Session):
        """Test successful user creation."""
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!"
        )
        
        response = create_user(db_session, user_data)
        
        # Verify response content
        assert response.status_code == 200
        response_data = response.body.decode()
        assert "testuser" in response_data
        assert "test@example.com" in response_data
        assert "User created successfully" in response_data
        
        # Verify user was actually created in database
        db_user = db_session.query(User).filter(User.email == "test@example.com").first()
        assert db_user is not None
        assert db_user.username == "testuser"
        assert db_user.is_admin is False
    
    def test_create_user_hashes_password(self, db_session: Session):
        """Test that user password is hashed before storage."""
        user_data = UserCreate(
            username="secureuser",
            email="secure@example.com",
            password="PlainTextPassword123!"
        )
        
        create_user(db_session, user_data)
        
        db_user = db_session.query(User).filter(User.email == "secure@example.com").first()
        # Password should be hashed, not plain text
        assert db_user.password != "PlainTextPassword123!"
        assert db_user.password.startswith("$2")  # Bcrypt hash
        # Verify password can be verified
        assert pwd_context.verify("PlainTextPassword123!", db_user.password)
    
    def test_create_user_duplicate_email(self, db_session: Session, test_user: User):
        """Test that duplicate email raises exception."""
        user_data = UserCreate(
            username="differentuser",
            email=test_user.email,  # Same email as existing user
            password="TestPassword123!"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            create_user(db_session, user_data)
        
        assert exc_info.value.status_code == 400
        assert "already registered" in str(exc_info.value.detail).lower()
    
    def test_create_user_as_admin(self, db_session: Session):
        """Test creating user with admin privileges."""
        user_data = UserCreate(
            username="adminuser",
            email="admin@example.com",
            password="AdminPassword123!"
        )
        
        response = create_user(db_session, user_data, isAdmin=True)
        
        db_user = db_session.query(User).filter(User.email == "admin@example.com").first()
        assert db_user.is_admin is True
    
    def test_create_user_initializes_storage(self, db_session: Session):
        """Test that new user has initial storage usage of 0."""
        user_data = UserCreate(
            username="newuser",
            email="newuser@example.com",
            password="TestPassword123!"
        )
        
        create_user(db_session, user_data)
        
        db_user = db_session.query(User).filter(User.email == "newuser@example.com").first()
        assert db_user.total_storage_used == 0.0
    
    def test_create_user_with_special_characters_in_email(self, db_session: Session):
        """Test user creation with special characters in email."""
        user_data = UserCreate(
            username="specialuser",
            email="user+tag@example.com",
            password="TestPassword123!"
        )
        
        response = create_user(db_session, user_data)
        assert response.status_code == 200
    
    def test_create_user_with_unicode_username(self, db_session: Session):
        """Test user creation with unicode characters in username."""
        user_data = UserCreate(
            username="用户123",  # Chinese characters
            email="unicode@example.com",
            password="TestPassword123!"
        )
        
        response = create_user(db_session, user_data)
        assert response.status_code == 200


class TestAuthenticateUser:
    """Test user authentication functionality."""
    
    def test_authenticate_user_success(self, db_session: Session, test_user: User):
        """Test successful user authentication."""
        # test_user fixture uses password "TestPassword123!"
        login_data = UserLogin(
            email=test_user.email,
            password="TestPassword123!"
        )
        
        response = authenticate_user(db_session, login_data)
        
        assert response.status_code == 200
        response_data = response.body.decode()
        assert "Welcome back" in response_data
        assert test_user.username in response_data
    
    def test_authenticate_user_updates_last_login(self, db_session: Session, test_user: User):
        """Test that last_login timestamp is updated on successful authentication."""
        original_last_login = test_user.last_login
        
        login_data = UserLogin(
            email=test_user.email,
            password="TestPassword123!"
        )
        
        authenticate_user(db_session, login_data)
        
        # Refresh user from database
        db_session.refresh(test_user)
        assert test_user.last_login != original_last_login
        assert test_user.last_login > original_last_login
    
    def test_authenticate_user_invalid_email(self, db_session: Session):
        """Test authentication with non-existent email."""
        login_data = UserLogin(
            email="nonexistent@example.com",
            password="AnyPassword123!"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            authenticate_user(db_session, login_data)
        
        assert exc_info.value.status_code == 401
        assert "Invalid email or password" in str(exc_info.value.detail)
    
    def test_authenticate_user_invalid_password(self, db_session: Session, test_user: User):
        """Test authentication with incorrect password."""
        login_data = UserLogin(
            email=test_user.email,
            password="WrongPassword123!"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            authenticate_user(db_session, login_data)
        
        assert exc_info.value.status_code == 401
        assert "Invalid email or password" in str(exc_info.value.detail)
    
    def test_authenticate_user_case_sensitive_password(self, db_session: Session, test_user: User):
        """Test that password verification is case-sensitive."""
        login_data = UserLogin(
            email=test_user.email,
            password="testpassword123!"  # lowercase instead of TestPassword123!
        )
        
        with pytest.raises(HTTPException) as exc_info:
            authenticate_user(db_session, login_data)
        
        assert exc_info.value.status_code == 401
    
    def test_authenticate_user_returns_storage_info(self, db_session: Session, test_user: User):
        """Test that authentication response includes user storage information."""
        login_data = UserLogin(
            email=test_user.email,
            password="TestPassword123!"
        )
        
        response = authenticate_user(db_session, login_data)
        response_data = response.body.decode()
        
        assert "user used storage" in response_data.lower()
    
    def test_authenticate_user_creates_analytics_event(self, db_session: Session, test_user: User):
        """Test that login creates an analytics event."""
        from app.models.analytics_event import AnalyticsEvent
        
        # Count events before login
        events_before = db_session.query(AnalyticsEvent).filter(
            AnalyticsEvent.user_id == test_user.id,
            AnalyticsEvent.event_type == "user_login"
        ).count()
        
        login_data = UserLogin(
            email=test_user.email,
            password="TestPassword123!"
        )
        
        authenticate_user(db_session, login_data)
        
        # Count events after login
        events_after = db_session.query(AnalyticsEvent).filter(
            AnalyticsEvent.user_id == test_user.id,
            AnalyticsEvent.event_type == "user_login"
        ).count()
        
        assert events_after == events_before + 1


class TestUpdateLastLogin:
    """Test last login timestamp update functionality."""
    
    def test_update_last_login_changes_timestamp(self, db_session: Session, test_user: User):
        """Test that update_last_login changes the last_login timestamp."""
        original_last_login = test_user.last_login
        
        update_last_login(db_session, test_user)
        
        db_session.refresh(test_user)
        assert test_user.last_login > original_last_login
    
    def test_update_last_login_creates_event(self, db_session: Session, test_user: User):
        """Test that update_last_login creates an analytics event."""
        from app.models.analytics_event import AnalyticsEvent
        
        events_before = db_session.query(AnalyticsEvent).count()
        
        update_last_login(db_session, test_user)
        
        events_after = db_session.query(AnalyticsEvent).count()
        assert events_after == events_before + 1
    
    def test_update_last_login_event_details(self, db_session: Session, test_user: User):
        """Test that login event contains correct details."""
        from app.models.analytics_event import AnalyticsEvent
        
        update_last_login(db_session, test_user)
        
        event = db_session.query(AnalyticsEvent).filter(
            AnalyticsEvent.user_id == test_user.id
        ).order_by(AnalyticsEvent.timestamp.desc()).first()
        
        assert event is not None
        assert event.event_type == "user_login"
        assert event.details["user_id"] == test_user.id
        assert event.details["username"] == test_user.username


class TestAuthenticationSecurity:
    """Test security aspects of authentication."""
    
    def test_error_messages_dont_leak_information(self, db_session: Session, test_user: User):
        """Test that error messages don't reveal whether email exists."""
        # Try with non-existent email
        login_data_1 = UserLogin(
            email="nonexistent@example.com",
            password="SomePassword123!"
        )
        
        # Try with existing email but wrong password
        login_data_2 = UserLogin(
            email=test_user.email,
            password="WrongPassword123!"
        )
        
        # Both should return same error message
        with pytest.raises(HTTPException) as exc_1:
            authenticate_user(db_session, login_data_1)
        
        with pytest.raises(HTTPException) as exc_2:
            authenticate_user(db_session, login_data_2)
        
        # Error messages should be identical (don't reveal if email exists)
        assert exc_1.value.detail == exc_2.value.detail
    
    def test_empty_password_rejected(self, db_session: Session, test_user: User):
        """Test that empty password is rejected."""
        login_data = UserLogin(
            email=test_user.email,
            password=""
        )
        
        with pytest.raises(HTTPException):
            authenticate_user(db_session, login_data)
    
    def test_sql_injection_attempt_in_email(self, db_session: Session):
        """Test that SQL injection attempts in email are handled safely."""
        # Use model_construct to bypass Pydantic validation to test DB layer security
        login_data = UserLogin.model_construct(
            email="' OR '1'='1",
            password="TestPassword123!"
        )
        
        with pytest.raises(ValueError) as exc_info:
            authenticate_user(db_session, login_data)
        
        assert "Potential SQL injection detected" in str(exc_info.value)
