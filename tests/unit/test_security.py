"""
Unit tests for security module.
Testing password hashing and authentication security in isolation.
"""
import pytest
from app.core.security import hash_password, pwd_context


class TestPasswordHashing:
    """Test password hashing functionality."""
    
    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        hashed = hash_password("TestPassword123!")
        assert isinstance(hashed, str)
        assert len(hashed) > 0
    
    def test_hash_password_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        hash1 = hash_password("Password123!")
        hash2 = hash_password("DifferentPass456!")
        assert hash1 != hash2
    
    def test_hash_password_same_password_different_salts(self):
        """Test that same password produces different hashes (different salts)."""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        # Bcrypt uses random salt, so same password should have different hashes
        assert hash1 != hash2
    
    def test_verify_correct_password(self):
        """Test that correct password verification works."""
        password = "CorrectPassword123!"
        hashed = hash_password(password)
        assert pwd_context.verify(password, hashed) is True
    
    def test_verify_incorrect_password(self):
        """Test that incorrect password verification fails."""
        password = "CorrectPassword123!"
        hashed = hash_password(password)
        assert pwd_context.verify("WrongPassword123!", hashed) is False
    
    def test_hash_password_handles_special_characters(self):
        """Test that passwords with special characters are handled correctly."""
        password = "P@ssw0rd!#$%^&*()"
        hashed = hash_password(password)
        assert pwd_context.verify(password, hashed) is True
    
    def test_hash_password_handles_unicode(self):
        """Test that passwords with unicode characters are handled."""
        password = "Пароль123!"  # Cyrillic
        hashed = hash_password(password)
        assert pwd_context.verify(password, hashed) is True
    
    def test_hash_password_empty_string(self):
        """Test that empty password can be hashed (edge case)."""
        hashed = hash_password("")
        assert isinstance(hashed, str)
        assert pwd_context.verify("", hashed) is True
    
    def test_hash_password_very_long_password(self):
        """Test that very long passwords are handled (truncated to 72 bytes)."""
        # Bcrypt has a 72-byte limit
        long_password = "a" * 100
        hashed = hash_password(long_password)
        # Should still verify with first 72 characters
        assert pwd_context.verify(long_password[:72], hashed) is True
    
    def test_hash_password_max_bcrypt_length(self):
        """Test that password exactly at bcrypt limit is handled."""
        password_72_chars = "a" * 72
        hashed = hash_password(password_72_chars)
        assert pwd_context.verify(password_72_chars, hashed) is True
    
    def test_hash_format_is_bcrypt(self):
        """Test that hash format follows bcrypt standard."""
        hashed = hash_password("TestPassword123!")
        # Bcrypt hashes start with $2b$ or $2a$ or $2y$
        assert hashed.startswith("$2")
        assert len(hashed) == 60  # Standard bcrypt hash length


class TestPasswordSecurityProperties:
    """Test security properties of password hashing."""
    
    def test_hashes_not_reversible(self):
        """Test that hashes cannot be reversed to original password."""
        password = "SecretPassword123!"
        hashed = hash_password(password)
        # Hash should not contain the original password
        assert password not in hashed
    
    def test_hash_timing_consistent(self):
        """Test that hash verification takes similar time (prevent timing attacks)."""
        import time
        
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        # Measure time for correct password
        start = time.time()
        pwd_context.verify(password, hashed)
        correct_time = time.time() - start
        
        # Measure time for incorrect password
        start = time.time()
        pwd_context.verify("WrongPassword!", hashed)
        incorrect_time = time.time() - start
        
        # Times should be similar (within 100ms difference)
        # Note: This is a rough check, timing attacks are complex
        assert abs(correct_time - incorrect_time) < 0.1
    
    def test_multiple_hashes_different_salts(self):
        """Test that bcrypt uses different salts for each hash."""
        password = "TestPassword123!"
        hashes = [hash_password(password) for _ in range(5)]
        
        # All hashes should be unique (different salts)
        assert len(set(hashes)) == 5


class TestPasswordEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_password_with_newlines(self):
        """Test handling of passwords with newline characters."""
        password = "Test\nPassword\r\n123"
        hashed = hash_password(password)
        assert pwd_context.verify(password, hashed) is True
    
    def test_password_with_tabs(self):
        """Test handling of passwords with tab characters."""
        password = "Test\tPassword\t123"
        hashed = hash_password(password)
        assert pwd_context.verify(password, hashed) is True
    
    def test_password_whitespace_only(self):
        """Test handling of whitespace-only passwords."""
        password = "     "
        hashed = hash_password(password)
        assert pwd_context.verify(password, hashed) is True
    
    def test_password_numbers_only(self):
        """Test handling of numeric-only passwords."""
        password = "123456789"
        hashed = hash_password(password)
        assert pwd_context.verify(password, hashed) is True


class TestPasswordContextConfiguration:
    """Test password context configuration."""
    
    def test_bcrypt_scheme_is_used(self):
        """Test that bcrypt scheme is configured."""
        schemes = pwd_context.schemes()
        assert "bcrypt" in schemes