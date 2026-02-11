"""
Integration tests for authentication router.
Testing auth endpoints with real HTTP requests and database interactions.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User


class TestSignupEndpoint:
    """Test /auth/signup endpoint."""
    
    def test_signup_success(self, client: TestClient, db_session: Session):
        """Test successful user registration."""
        response = client.post(
            "/auth/signup",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "NewPassword123!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "message" in data
        assert data["message"] == "User created successfully"
        assert "password" not in data  # Password should never be in response
    
    def test_signup_returns_user_id(self, client: TestClient):
        """Test that signup returns user ID."""
        response = client.post(
            "/auth/signup",
            json={
                "username": "iduser",
                "email": "iduser@example.com",
                "password": "Password123!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert isinstance(data["id"], int)
    
    def test_signup_duplicate_email(self, client: TestClient, test_user: User):
        """Test that duplicate email returns error."""
        response = client.post(
            "/auth/signup",
            json={
                "username": "different",
                "email": test_user.email,
                "password": "Password123!"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["detail"].lower()
    
    def test_signup_invalid_email_format(self, client: TestClient):
        """Test that invalid email format is rejected."""
        response = client.post(
            "/auth/signup",
            json={
                "username": "testuser",
                "email": "not-an-email",
                "password": "Password123!"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_signup_missing_fields(self, client: TestClient):
        """Test that missing required fields return validation error."""
        response = client.post(
            "/auth/signup",
            json={
                "username": "incomplete"
                # Missing email and password
            }
        )
        
        assert response.status_code == 422
    
    def test_signup_empty_password(self, client: TestClient):
        """Test that empty password is rejected."""
        response = client.post(
            "/auth/signup",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": ""
            }
        )
        
        assert response.status_code == 422
    
    def test_signup_with_special_characters(self, client: TestClient):
        """Test signup with special characters in username."""
        response = client.post(
            "/auth/signup",
            json={
                "username": "user_name-123",
                "email": "special@example.com",
                "password": "Password123!"
            }
        )
        
        assert response.status_code == 200
    
    def test_signup_case_sensitive_email(self, client: TestClient, test_user: User):
        """Test that email comparison is case-insensitive."""
        response = client.post(
            "/auth/signup",
            json={
                "username": "newuser",
                "email": test_user.email.upper(),
                "password": "Password123!"
            }
        )
        
        # Should be rejected as duplicate (case-insensitive)
        assert response.status_code == 400


class TestLoginEndpoint:
    """Test /auth/login endpoint."""
    
    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful login."""
        response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPassword123!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Welcome back" in data["message"]
        assert test_user.username in data["message"]
        assert "token" in data
        assert "user_id" in data
    
    def test_login_returns_user_info(self, client: TestClient, test_user: User):
        """Test that login returns user information."""
        response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPassword123!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == test_user.id
        assert "user used storage" in data
    
    def test_login_invalid_email(self, client: TestClient):
        """Test login with non-existent email."""
        response = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "AnyPassword123!"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid email or password" in data["detail"]
    
    def test_login_invalid_password(self, client: TestClient, test_user: User):
        """Test login with incorrect password."""
        response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "WrongPassword123!"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid email or password" in data["detail"]
    
    def test_login_updates_last_login(self, client: TestClient, test_user: User, db_session: Session):
        """Test that login updates last_login timestamp."""
        original_last_login = test_user.last_login
        
        response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPassword123!"
            }
        )
        
        assert response.status_code == 200
        
        # Refresh user from database
        db_session.refresh(test_user)
        assert test_user.last_login > original_last_login # type: ignore
    
    def test_login_missing_fields(self, client: TestClient):
        """Test login with missing fields."""
        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com"
                # Missing password
            }
        )
        
        assert response.status_code == 422
    
    def test_login_empty_password(self, client: TestClient, test_user: User):
        """Test login with empty password."""
        response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": ""
            }
        )
        
        assert response.status_code == 422 or response.status_code == 401
    
    def test_login_multiple_attempts(self, client: TestClient, test_user: User):
        """Test multiple login attempts (no lockout for now)."""
        # This test documents current behavior - no rate limiting
        for _ in range(5):
            response = client.post(
                "/auth/login",
                json={
                    "email": test_user.email,
                    "password": "WrongPassword!"
                }
            )
            assert response.status_code == 401
        
        # Successful login should still work
        response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPassword123!"
            }
        )
        assert response.status_code == 200


class TestAuthenticationFlow:
    """Test complete authentication flows."""
    
    def test_signup_then_login(self, client: TestClient):
        """Test complete signup and login flow."""
        # Step 1: Signup
        signup_response = client.post(
            "/auth/signup",
            json={
                "username": "flowuser",
                "email": "flowuser@example.com",
                "password": "FlowPassword123!"
            }
        )
        assert signup_response.status_code == 200
        user_id = signup_response.json()["id"]
        
        # Step 2: Login with same credentials
        login_response = client.post(
            "/auth/login",
            json={
                "email": "flowuser@example.com",
                "password": "FlowPassword123!"
            }
        )
        assert login_response.status_code == 200
        assert login_response.json()["user_id"] == user_id
    
    def test_signup_login_logout_flow(self, client: TestClient):
        """Test signup, login, and verify token flow."""
        # Signup
        signup_response = client.post(
            "/auth/signup",
            json={
                "username": "completeuser",
                "email": "complete@example.com",
                "password": "CompletePassword123!"
            }
        )
        assert signup_response.status_code == 200
        
        # Login
        login_response = client.post(
            "/auth/login",
            json={
                "email": "complete@example.com",
                "password": "CompletePassword123!"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # TODO: Once JWT is implemented, verify token can be used
        assert "token" in login_response.json()


class TestAuthenticationSecurity:
    """Test security aspects of authentication endpoints."""
    
    def test_password_not_in_response(self, client: TestClient):
        """Test that passwords are never included in responses."""
        response = client.post(
            "/auth/signup",
            json={
                "username": "secureuser",
                "email": "secure@example.com",
                "password": "SecurePassword123!"
            }
        )
        
        assert response.status_code == 200
        response_text = response.text.lower()
        assert "securepassword123" not in response_text
    
    def test_error_messages_consistent(self, client: TestClient, test_user: User):
        """Test that error messages don't reveal user existence."""
        # Invalid email
        response1 = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "Password123!"
            }
        )
        
        # Valid email, wrong password
        response2 = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "WrongPassword!"
            }
        )
        
        # Both should return same status and similar message
        assert response1.status_code == response2.status_code == 401
        assert response1.json()["detail"] == response2.json()["detail"]
    
    @pytest.mark.skip(reason="Not implemented yet")
    def test_sql_injection_protection(self, client: TestClient):
        """Test that SQL injection attempts are handled safely."""
        response = client.post(
            "/auth/login",
            json={
                "email": "' OR '1'='1",
                "password": "password"
            }
        )
        
        assert response.status_code == 401
   
    @pytest.mark.skip(reason="Not implemented yet")     
    def test_xss_protection_in_username(self, client: TestClient):
        """Test that XSS attempts in username are handled."""
        response = client.post(
            "/auth/signup",
            json={
                "username": "<script>alert('xss')</script>",
                "email": "xss@example.com",
                "password": "Password123!"
            }
        )
        
        # Should either succeed with sanitized input or fail validation
        # Either way, script should not be executable
        if response.status_code == 200:
            data = response.json()
            # Verify script tags are escaped or removed
            username = data["username"]
            assert username != "<script>alert('xss')</script>"


class TestAuthenticationEdgeCases:
    """Test edge cases in authentication."""
    
    def test_very_long_username(self, client: TestClient):
        """Test handling of very long usernames."""
        long_username = "a" * 1000
        response = client.post(
            "/auth/signup",
            json={
                "username": long_username,
                "email": "long@example.com",
                "password": "Password123!"
            }
        )
        
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 422, 400]
    
    def test_unicode_in_credentials(self, client: TestClient):
        """Test unicode characters in credentials."""
        response = client.post(
            "/auth/signup",
            json={
                "username": "用户名",
                "email": "unicode@example.com",
                "password": "Password123!"
            }
        )
        
        # Should handle unicode gracefully
        assert response.status_code in [200, 422]
    
    def test_whitespace_in_email(self, client: TestClient):
        """Test handling of whitespace in email."""
        response = client.post(
            "/auth/signup",
            json={
                "username": "testuser",
                "email": "  test@example.com  ",
                "password": "Password123!"
            }
        )
        
        # Pydantic should handle whitespace stripping
        assert response.status_code in [200, 422]
